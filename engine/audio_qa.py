"""Audio QA: beat alignment, silence, loudness proxy, and visual spectrogram."""
from __future__ import annotations

import json
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

SR = 44100
ROOT = Path(__file__).resolve().parents[1]


def load(path: Path):
    with wave.open(str(path), "rb") as f:
        n = f.getnframes()
        ch = f.getnchannels()
        data = np.frombuffer(f.readframes(n), dtype="<i2").astype(np.float32) / 32768
    return data.reshape(-1, ch).T


def colormap(v: np.ndarray) -> np.ndarray:
    # compact inferno-like ramp
    stops = np.array(
        [[0, 0, 4], [40, 11, 84], [101, 21, 110], [159, 42, 99], [212, 72, 66], [245, 125, 21], [250, 193, 39], [252, 255, 164]],
        dtype=np.float32,
    )
    pos = np.linspace(0, 1, len(stops))
    out = np.zeros(v.shape + (3,), dtype=np.uint8)
    for c in range(3):
        out[..., c] = np.interp(v, pos, stops[:, c]).astype(np.uint8)
    return out


def spectrogram(mono: np.ndarray, path: Path, title: str):
    win, hop = 2048, 512
    frames = []
    for i in range(0, len(mono) - win, hop):
        seg = mono[i : i + win] * np.hanning(win)
        frames.append(np.abs(np.fft.rfft(seg)))
    spec = np.array(frames).T
    freqs = np.fft.rfftfreq(win, 1 / SR)
    # log-frequency resample 40..16000 to 260 rows
    edges = np.geomspace(40, 16000, 261)
    rows = []
    for b in range(260):
        m = (freqs >= edges[b]) & (freqs < edges[b + 1])
        rows.append(spec[m].mean(axis=0) if m.any() else np.zeros(spec.shape[1]))
    rows = np.array(rows)
    db = 20 * np.log10(rows + 1e-9)
    v = np.clip((db - (db.max() - 70)) / 70, 0, 1)
    img = Image.fromarray(colormap(v)).resize((1600, 300))

    # waveform strip
    H, W = 120, 1600
    wave_img = Image.new("RGB", (W, H), (8, 8, 20))
    d = ImageDraw.Draw(wave_img)
    d.line([(0, H // 2), (W, H // 2)], fill=(40, 40, 70))
    step = max(1, len(mono) // W)
    for x in range(W):
        seg = mono[x * step : (x + 1) * step]
        if len(seg):
            a = int(np.max(np.abs(seg)) * (H // 2 - 6))
            d.line([(x, H // 2 - a), (x, H // 2 + a)], fill=(201, 169, 106))
    canvas = Image.new("RGB", (W, 460), (5, 5, 16))
    canvas.paste(wave_img, (0, 0))
    canvas.paste(img, (0, 130))
    d = ImageDraw.Draw(canvas)
    d.text((12, 8), title, fill=(234, 234, 242))
    d.text((12, 26), f"duration {len(mono)/SR:.2f}s  peak {20*np.log10(np.max(np.abs(mono))+1e-9):.1f} dBFS", fill=(138, 138, 160))
    canvas.save(path)


def onsets(mono: np.ndarray, lo=150.0) -> np.ndarray:
    # crude low-band energy flux
    from scipy.signal import butter, sosfilt

    sos = butter(2, lo / (SR / 2), btype="low", output="sos")
    low = sosfilt(sos, mono)
    env = np.abs(low)
    # 10ms rms
    k = int(0.01 * SR)
    env = np.convolve(env, np.ones(k) / k, mode="same")
    flux = np.diff(env, prepend=env[0])
    flux = np.maximum(flux, 0)
    thresh = np.percentile(flux, 99.0)
    peaks = []
    min_gap = int(0.25 * SR)
    i = 0
    while i < len(flux):
        if flux[i] >= thresh:
            j = min(len(flux), i + min_gap)
            p = i + int(np.argmax(flux[i:j]))
            peaks.append(p / SR)
            i = j
        else:
            i += 1
    return np.array(peaks)


def comb_alignment(mono: np.ndarray, beat: float, start: float, end: float, lo: float = 130.0) -> dict:
    """Correlate a low-band envelope with an impulse comb at the score's beat grid."""
    from scipy.signal import butter, sosfilt

    end = min(end, len(mono) / SR)
    sos = butter(2, lo / (SR / 2), btype="low", output="sos")
    low = np.abs(sosfilt(sos, mono))
    k = 44  # ~1 ms smoothing
    env = np.convolve(low, np.ones(k) / k, mode="same")
    times = np.arange(start, end, beat)
    best_lag, best_score = 0.0, -1.0
    for lag in np.arange(-0.06, 0.0601, 0.001):
        idx = ((times + lag) * SR).astype(int)
        idx = idx[(idx >= 0) & (idx < len(env))]
        if not len(idx):
            continue
        score = float(env[idx].mean())
        if score > best_score:
            best_lag, best_score = float(lag), score
    baseline = float(env[int(start * SR) : int(end * SR)].mean())
    return {
        "lag_ms": round(best_lag * 1000, 1),
        "beat_contrast": round(best_score / (baseline + 1e-9), 2),
        "beats_checked": int(len(times)),
    }


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


def main():
    qa_dir = ROOT / "qa" / "audio"
    qa_dir.mkdir(parents=True, exist_ok=True)
    report = {}
    for name in ("knowledge", "beat", "music"):
        wav = ROOT / "projects" / name / "audio.wav"
        meta = json.loads((wav.parent / "audio.json").read_text(encoding="utf-8"))
        x = load(wav)
        mono = x.mean(axis=0)
        dur = len(mono) / SR
        # silence: 50ms windows below -60 dBFS
        k = int(0.05 * SR)
        rms = np.sqrt(np.convolve(mono**2, np.ones(k) / k, mode="same"))
        silent = float(np.mean(rms < 1e-3))
        # clipping samples
        clip = float(np.mean(np.abs(mono) > 0.999))
        beat = meta["beat_seconds"]
        ranges = {"knowledge": (64.0, 96.0), "beat": (0.0, 22.5), "music": (6.0, 24.0)}
        align = comb_alignment(mono, beat, *ranges[name])
        loud = ebur128(wav)
        spectrogram(mono, qa_dir / f"{name}.png", f"{name} · {meta['bpm']} BPM · {meta['key']}")
        report[name] = {
            "duration": round(dur, 3),
            "peak_dbfs": round(float(20 * np.log10(np.max(np.abs(mono)) + 1e-9)), 2),
            "silence_ratio": round(silent, 4),
            "clip_ratio": round(clip, 6),
            "beat_alignment": align,
            "loudness": loud,
            "sha256": meta["sha256"],
            "score_bpm": meta["bpm"],
        }
        print(name, json.dumps(report[name], ensure_ascii=False))
    (qa_dir / "audio-qa.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
