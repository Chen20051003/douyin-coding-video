"""Generate the voiceover with Edge TTS and build a per-line timing map."""
from __future__ import annotations

import asyncio
import json
import subprocess
import wave
from pathlib import Path

import numpy as np
from scipy.signal import butter, sosfilt

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
PROJ = ROOT / "projects" / "yuanfen"
VOICE_DIR = PROJ / "voice"
SR = 44100


def ffprobe_duration(path: Path) -> float:
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return float(json.loads(p.stdout)["format"]["duration"])


def decode(mp3: Path, wav: Path):
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(mp3), "-ar", str(SR), "-ac", "1", str(wav)],
        check=True,
    )


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as f:
        return np.frombuffer(f.readframes(f.getnframes()), dtype="<i2").astype(np.float32) / 32768.0


async def synthesize(text: str, voice: str, rate: str, pitch: str, out: Path):
    last = None
    for attempt in range(3):
        try:
            await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(str(out))
            return
        except Exception as e:  # noqa: BLE001
            last = e
            await asyncio.sleep(1.2 * (attempt + 1))
    raise RuntimeError(f"TTS failed: {text} ({last})")


def process_voice(buf: np.ndarray) -> np.ndarray:
    # gentle cleanup + presence, then a short plate so it does not sound dry
    sos = butter(2, 85 / (SR / 2), btype="high", output="sos")
    x = sosfilt(sos, buf)
    sos = butter(2, 13000 / (SR / 2), btype="low", output="sos")
    x = sosfilt(sos, x)

    band = butter(2, [2200 / (SR / 2), 5200 / (SR / 2)], btype="band", output="sos")
    x = x + 0.22 * sosfilt(band, x)

    x = np.tanh(x * 1.25) / np.tanh(1.25)
    peak = float(np.max(np.abs(x))) or 1.0
    x = x / peak * 0.92

    n_ir = int(1.4 * SR)
    t = np.arange(n_ir) / SR
    rng = np.random.default_rng(11)
    ir = rng.normal(0, 1, n_ir) * np.exp(-t / 0.55)
    ir = sosfilt(butter(2, 4500 / (SR / 2), btype="low", output="sos"), ir)
    ir[: int(0.01 * SR)] *= np.linspace(0, 1, int(0.01 * SR))
    ir /= np.max(np.abs(ir)) + 1e-9
    from scipy.signal import fftconvolve
    wet = fftconvolve(x, ir, mode="full")[: len(x)]
    wet /= np.max(np.abs(wet)) + 1e-9
    return (1 - 0.11) * x + 0.11 * wet


async def main():
    cfg = json.loads((PROJ / "script.json").read_text(encoding="utf-8"))
    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    lines = cfg["lines"]
    timings = []
    cursor = float(cfg.get("intro", 1.2))

    for i, line in enumerate(lines):
        mp3 = VOICE_DIR / f"line_{i:02d}.mp3"
        wav = VOICE_DIR / f"line_{i:02d}.wav"
        await synthesize(line["cn"], cfg["voice"], cfg["rate"], cfg["pitch"], mp3)
        decode(mp3, wav)
        dur = ffprobe_duration(wav)
        start = cursor
        end = start + dur
        timings.append({
            "i": i,
            "cn": line["cn"],
            "en": line["en"],
            "scene": line["scene"],
            "start": round(start, 3),
            "end": round(end, 3),
            "duration": round(dur, 3),
            "file": f"voice/line_{i:02d}.wav",
        })
        cursor = end + float(line.get("pause_after", 0.45))
        print(f"{i:02d} {start:6.2f}-{end:6.2f}  {line['cn']}", flush=True)

    total = cursor + float(cfg.get("outro", 4.0))
    n = int(total * SR)
    buf = np.zeros(n, dtype=np.float32)
    for line, tm in zip(lines, timings):
        sig = read_wav(VOICE_DIR / f"line_{tm['i']:02d}.wav")
        a = int(tm["start"] * SR)
        b = min(n, a + len(sig))
        if b <= a:
            continue
        seg = sig[: b - a].copy()
        fade = min(int(0.012 * SR), len(seg) // 2)
        if fade:
            seg[:fade] *= np.linspace(0, 1, fade)
            seg[-fade:] *= np.linspace(1, 0, fade)
        buf[a:b] += seg

    buf = process_voice(buf)
    # trim trailing silence, then add a short tail
    nz = np.flatnonzero(np.abs(buf) > 1e-3)
    if len(nz):
        buf = buf[: min(len(buf), nz[-1] + int(1.2 * SR))]
    stereo = np.stack([buf, buf], axis=0)
    stereo = np.clip(stereo, -1, 1)

    with wave.open(str(PROJ / "voice.wav"), "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes((stereo.T * 32767).astype("<i2").tobytes())

    duration = round(len(buf) / SR, 3)
    meta = {
        "title": cfg["title"],
        "voice": cfg["voice"],
        "rate": cfg["rate"],
        "pitch": cfg["pitch"],
        "duration": duration,
        "bpm": 104,
        "lines": timings,
    }
    (PROJ / "timing.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    (PROJ / "timing.js").write_text("window.TIMING=" + json.dumps(meta, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(f"voice total {duration:.2f}s -> {PROJ / 'voice.wav'}")


if __name__ == "__main__":
    asyncio.run(main())
