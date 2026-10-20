"""Final MP4 QA: probe, black/silence, loudness, motion density, sampled frames."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)


def ffprobe(path: Path) -> dict:
    p = run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)])
    return json.loads(p.stdout)


def ebur128(path: Path) -> dict:
    p = run(["ffmpeg", "-nostats", "-i", str(path), "-filter_complex", "ebur128=peak=true", "-f", "null", "-"])
    txt = p.stderr
    out = {}
    for key, label in (("I:", "integrated_lufs"), ("LRA:", "lra"), ("Peak:", "true_peak_db")):
        vals = [ln.split(key)[-1].strip().split()[0] for ln in txt.splitlines() if key in ln]
        if vals:
            try:
                out[label] = float(vals[-1])
            except ValueError:
                pass
    return out


def detect(path: Path, kind: str) -> list:
    if kind == "black":
        vf = "blackdetect=d=0.2:pix_th=0.02:pic_th=0.98"
    else:
        vf = "silencedetect=n=-45dB:d=0.35"
    p = run(["ffmpeg", "-hide_banner", "-i", str(path), "-vf" if kind == "black" else "-af", vf, "-f", "null", "-"])
    return [ln for ln in p.stderr.splitlines() if ("black_start" in ln or "silence_start" in ln)]


def extract(path: Path, out: Path, t: float):
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(path), "-frames:v", "1", str(out)])


def contact_sheet(paths: list[Path], out: Path, label: str):
    thumbs = [Image.open(p).convert("RGB") for p in paths]
    tw = 480
    th = int(thumbs[0].height * tw / thumbs[0].width)
    thumbs = [im.resize((tw, th)) for im in thumbs]
    sheet = Image.new("RGB", (tw * len(thumbs), th + 40), (8, 8, 18))
    d = ImageDraw.Draw(sheet)
    for i, im in enumerate(thumbs):
        sheet.paste(im, (i * tw, 40))
    d.text((10, 10), label, fill=(230, 230, 240))
    sheet.save(out)


def motion(path: Path, w: int, h: int):
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(path), "-vf", f"fps=2,scale={w}:{h}", "-q:v", "6", str(td / "%04d.jpg")])
        files = sorted(td.glob("*.jpg"))
        if len(files) < 3:
            return {}
        prev = None
        vals = []
        for f in files:
            a = np.asarray(Image.open(f).convert("L"), dtype=np.float32)
            if prev is not None:
                vals.append(float(np.mean(np.abs(a - prev))))
            prev = a
        vals = np.array(vals)
        return {
            "samples": int(len(vals)),
            "mean_diff": round(float(vals.mean()), 2),
            "median_diff": round(float(np.median(vals)), 2),
            "static_ratio": round(float(np.mean(vals < 1.0)), 3),
        }


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    path = Path(a.file)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    probe = ffprobe(path)
    vs = next((s for s in probe["streams"] if s["codec_type"] == "video"), {})
    au = next((s for s in probe["streams"] if s["codec_type"] == "audio"), {})
    dur = float(probe["format"].get("duration", 0))
    fps = vs.get("avg_frame_rate", "0/1")
    num, den = (int(x) for x in fps.split("/")) if "/" in fps else (0, 1)
    fps_val = round(num / den, 3) if den else 0

    frames_dir = ROOT = Path(r"C:\Users\32768\Desktop\douyin-coding-video")
    qa_dir = out
    pcts = [0.1, 0.25, 0.5, 0.75, 0.9]
    imgs = []
    for p in pcts:
        f = qa_dir / f"frame_{int(p*100):02d}.png"
        extract(path, f, dur * p)
        imgs.append(f)
    contact_sheet(imgs, qa_dir / "contact.png", f"{path.name} · {dur:.2f}s · {vs.get('width')}x{vs.get('height')}")

    motion_stats = motion(path, 480 if vs.get("width", 0) >= 1000 else 360, 270 if vs.get("height", 0) <= 1080 else 640)
    report = {
        "file": str(path),
        "sha256": sha256(path),
        "duration": round(dur, 3),
        "video": {
            "codec": vs.get("codec_name"),
            "profile": vs.get("profile"),
            "width": vs.get("width"),
            "height": vs.get("height"),
            "pix_fmt": vs.get("pix_fmt"),
            "fps": fps_val,
            "nb_frames": vs.get("nb_frames"),
        },
        "audio": {
            "codec": au.get("codec_name"),
            "sample_rate": au.get("sample_rate"),
            "channels": au.get("channels"),
            "bit_rate": au.get("bit_rate"),
        },
        "loudness": ebur128(path),
        "black_events": detect(path, "black"),
        "silence_events": detect(path, "silence"),
        "motion": motion_stats,
        "sampled_frames": [str(p) for p in imgs],
        "contact_sheet": str(qa_dir / "contact.png"),
    }
    (qa_dir / "qa.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
