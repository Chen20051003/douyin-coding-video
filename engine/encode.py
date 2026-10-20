"""Encode a JPEG frame sequence + WAV into a Douyin-ready MP4 with loudness trim."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


def ebur128(path: Path) -> dict:
    cmd = ["ffmpeg", "-nostats", "-i", str(path), "-filter_complex", "ebur128=peak=true", "-f", "null", "-"]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
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


def encode(frames: Path, audio: Path, out: Path, fps: int, target_lufs: float, crf: int = 18, limit: float = 0.891):
    loud = ebur128(audio)
    gain = target_lufs - loud.get("integrated_lufs", target_lufs)
    peak = loud.get("true_peak_db", -1.0)
    if peak + gain > -2.0:
        gain = -2.0 - peak
    gain = round(max(-18.0, min(18.0, gain)), 2)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-framerate", str(fps), "-i", str(frames / "%06d.jpg"),
        "-i", str(audio),
        "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
        "-vf", "scale=in_range=full:out_range=tv,format=yuv420p",
        "-pix_fmt", "yuv420p", "-color_range", "tv", "-profile:v", "high", "-level", "4.2",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-af", f"volume={gain}dB,alimiter=limit={limit}:level=false",
        "-shortest", "-movflags", "+faststart",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    final = ebur128(out)
    info = {
        "output": str(out),
        "gain_db": gain,
        "target_lufs": target_lufs,
        "input_loudness": loud,
        "output_loudness": final,
        "size_mb": round(out.stat().st_size / 1024 / 1024, 2),
    }
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", required=True)
    ap.add_argument("--audio", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--lufs", type=float, default=-14.0)
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--limit", type=float, default=0.891)
    a = ap.parse_args()
    info = encode(Path(a.frames), Path(a.audio), Path(a.out), a.fps, a.lufs, a.crf, a.limit)
    out = Path(a.out)
    (out.parent / (out.stem + ".encode.json")).write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
