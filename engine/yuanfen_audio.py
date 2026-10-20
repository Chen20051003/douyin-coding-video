"""120 BPM score for <未见面的缘分> + voiceover ducking mix.

The drum book is deliberately different from the earlier films:
- taiko ostinato (0, 1.5, 2, 3.25 beats) instead of a plain four-on-floor
- four-on-floor kick only from the "light" section, ghost kick in the peak
- 16th snare roll into the two big drops, cymbal swells on section changes
"""
from __future__ import annotations

import hashlib
import json
import wave
from pathlib import Path

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

from audio import SR, bass_note, hat, kick, normalize, pad_chord, piano, place, riser, snare

ROOT = Path(__file__).resolve().parents[1]
PROJ = ROOT / "projects" / "yuanfen"
BPM = 112
BEAT = 60 / BPM
BAR = BEAT * 4


def taiko(dur: float = 0.55, f0: float = 92.0, f1: float = 50.0) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t / 0.045)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.24)
    skin = np.random.default_rng(7).normal(0, 1, n) * np.exp(-t / 0.035) * 0.35
    skin = sosfilt(butter(2, 900 / (SR / 2), btype="low", output="sos"), skin)
    return np.tanh((body + skin) * 1.5)


def clap(dur: float = 0.22) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(23)
    out = np.zeros(n)
    for delay, gain in ((0.0, 1.0), (0.011, 0.7), (0.023, 0.45)):
        i = int(delay * SR)
        seg = rng.normal(0, 1, n - i) * np.exp(-t[: n - i] / 0.055) * gain
        out[i:] += seg
    out = sosfilt(butter(2, [900 / (SR / 2), 7000 / (SR / 2)], btype="band", output="sos"), out)
    return np.tanh(out * 1.2)


def cymbal(dur: float = 2.4) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = np.random.default_rng(31).normal(0, 1, n)
    noise = sosfilt(butter(2, 5000 / (SR / 2), btype="high", output="sos"), noise)
    return noise * np.exp(-t / 0.75) * 0.5


def string_note(freq: float, dur: float, bright: float = 2600.0) -> np.ndarray:
    n = int(dur * SR)
    out = np.zeros(n)
    for det in (-0.004, 0.0, 0.004):
        t = np.arange(n) / SR
        out += 2 * ((freq * (1 + det) * t) % 1.0) - 1
    out = sosfilt(butter(2, bright / (SR / 2), btype="low", output="sos"), out)
    env = np.minimum(np.arange(n) / (0.25 * SR), 1) * np.minimum((n - np.arange(n)) / (0.5 * SR), 1)
    return normalize(out * env, 1.0)


def section_at(t: float, bounds: list[float], labels: list[str]) -> str:
    for i in range(len(labels)):
        if bounds[i] <= t < bounds[i + 1]:
            return labels[i]
    return labels[-1]


def compose(duration: float, bounds: list[float], labels: list[str]):
    n = int(duration * SR)
    dry = np.zeros((2, n))
    wet = np.zeros((2, n))

    prog = [
        ("Fm", [174.61, 207.65, 261.63, 349.23], 87.31),
        ("Db", [138.59, 174.61, 207.65, 277.18], 69.30),
        ("Ab", [207.65, 261.63, 311.13, 415.30], 103.83),
        ("Eb", [155.56, 196.00, 233.08, 311.13], 77.78),
    ]

    starts = [bounds[i] for i in range(len(labels))]
    def idx(t):
        return max(i for i, s in enumerate(starts) if t >= s)

    beats_total = int(np.ceil(duration / BEAT))
    for bi in range(beats_total):
        t0 = bi * BEAT
        if t0 >= duration:
            break
        bar_i = int(t0 // BAR)
        name, tones, root = prog[bar_i % 4]
        sec = section_at(t0, bounds, labels)
        e = {"hook": 0.18, "question": 0.38, "answer": 0.55, "light": 0.72,
             "distance": 0.55, "sync": 0.92, "line": 1.0, "outro": 0.35}[sec]
        beat_in_bar = (bi % 4)

        # pad / choir
        if beat_in_bar == 0:
            pad = pad_chord(tones, BAR + 0.2, 1350 + 500 * e)
            place(dry, pad, t0, 0, 0.05 + 0.05 * e)
            place(wet, pad, t0, 0, 0.06 + 0.05 * e)
            if e >= 0.9:
                choir = pad_chord([f * 2 for f in tones], BAR + 0.3, 1900)
                place(dry, choir, t0, 0, 0.035)
                place(wet, choir, t0, 0, 0.05)

        # piano motif
        if sec != "hook" or beat_in_bar == 0:
            if sec in ("hook", "outro"):
                note = piano(tones[2], 4.2, 0.7)
                place(dry, note, t0, 0.0, 0.055)
                place(wet, note, t0, 0.0, 0.12)
            else:
                pattern = [0, 2, 1, 3] if sec in ("question", "answer") else [0, 2, 3, 1]
                f = tones[pattern[beat_in_bar % 4]] * (2 if beat_in_bar == 3 else 1)
                note = piano(f, 2.4, 0.65)
                place(dry, note, t0, -0.18 if beat_in_bar % 2 else 0.18, 0.09 + 0.02 * e)
                place(wet, note, t0, 0, 0.1)

        # 8th-note piano ostinato: the engine of the "燃" sections
        if sec in ("light", "distance", "sync", "line"):
            for k in range(8):
                tt = t0 + k * BEAT / 2
                if tt >= duration:
                    break
                f = tones[(0, 2, 1, 3, 2, 1, 3, 2)[k]] * (2 if k % 4 == 3 else 1)
                nn = piano(f, 0.9, 0.5)
                place(dry, nn, tt, -0.25 if k % 2 else 0.25, 0.035 + 0.01 * e)
                place(wet, nn, tt, 0, 0.05)

        # strings
        if sec in ("answer", "light", "distance", "sync", "line", "outro"):
            if beat_in_bar == 0:
                st = string_note(root * 2, BAR + 0.1, 1800 + 700 * e)
                place(dry, st, t0, 0, 0.05 + 0.03 * e)
                place(wet, st, t0, 0, 0.06)
            if sec in ("sync", "line"):
                for k in range(2):
                    tt = t0 + k * BEAT / 2
                    if tt >= duration:
                        break
                    f = tones[(0, 2)[k]] * 2
                    os_ = string_note(f, BEAT / 2 * 0.85, 2200)
                    place(dry, os_, tt, -0.25 if k % 2 else 0.25, 0.032)
                    place(wet, os_, tt, 0, 0.04)

        # bass
        if sec in ("light", "distance", "sync", "line"):
            f = root * (2 if beat_in_bar == 3 else 1)
            place(dry, bass_note(f, BEAT * 0.8, 180), t0, 0, 0.24 + 0.05 * e)

        # drums: steady 8th-note taiko pulse (reference DNA), kick on 1/3
        if sec == "hook":
            if beat_in_bar in (0, 2):
                place(dry, kick(0.5, 100, 42), t0, 0, 0.32)
                place(dry, taiko(0.55, 90, 50), t0, -0.1, 0.20)
        else:
            for k in range(2):
                tt = t0 + k * BEAT / 2
                g = 0.30 if (beat_in_bar in (0, 2) and k == 0) else 0.16
                place(dry, taiko(0.38, 95, 52), tt, -0.15 if k == 0 else 0.15, g)
            if beat_in_bar in (0, 2):
                place(dry, kick(0.45, 115, 45), t0, 0, 0.40)
            if beat_in_bar in (1, 3):
                place(dry, clap(), t0, 0.1, 0.22 if sec in ("question", "answer") else 0.28)
            if sec in ("sync", "line") and beat_in_bar == 3:
                place(dry, taiko(0.3, 120, 62), t0 + BEAT * 0.25, 0.2, 0.22)
        if sec == "outro" and beat_in_bar in (0, 2):
            place(dry, taiko(0.7, 80, 45), t0, -0.1, 0.22)

        # hats
        if sec in ("light", "distance", "sync", "line"):
            place(dry, hat(0.03), t0 + BEAT / 2, 0.3, 0.04 + 0.02 * e)
            if sec in ("sync", "line"):
                place(dry, hat(0.02), t0 + BEAT / 4, -0.3, 0.02)

    # build rolls into the two drops
    for target, length in ((bounds[3], 2.0), (bounds[5], 3.0), (bounds[6], 2.0)):
        t = target - length
        k = 0
        while t < target - 0.04 and t < duration:
            g = 0.08 + 0.28 * (t - (target - length)) / length
            place(dry, snare(0.12, 220), t, 0.1, g)
            place(wet, snare(0.12, 220), t, 0.1, g * 0.7)
            t += 0.055
            k += 1
        place(dry, riser(length), target - length, 0, 0.18)

    for t in (bounds[3], bounds[5], bounds[6], bounds[7]):
        if t < duration:
            place(dry, cymbal(2.6), t, 0, 0.25)
            place(dry, kick(0.9, 110, 38), t, 0, 0.55)
            place(wet, cymbal(2.6), t, 0, 0.15)

    wet_sum = np.zeros_like(dry)
    for ch in range(2):
        wet_sum[ch] = fftconvolve(wet[ch], _ir(), mode="full")[:n]
    wet_sum = normalize(wet_sum, 1.0)
    mix = dry + 0.4 * wet_sum
    mix = np.tanh(mix * 1.12) / np.tanh(1.12)
    mix = normalize(mix, 0.9)

    # fades
    fi, fo = int(0.4 * SR), int(3.0 * SR)
    mix[:, :fi] *= np.linspace(0, 1, fi) ** 0.7
    mix[:, -fo:] *= np.linspace(1, 0, fo) ** 1.2
    return mix


def _ir() -> np.ndarray:
    n = int(2.2 * SR)
    t = np.arange(n) / SR
    ir = np.random.default_rng(5).normal(0, 1, n) * np.exp(-t / 1.1)
    ir = sosfilt(butter(2, 4200 / (SR / 2), btype="low", output="sos"), ir)
    ir[: int(0.015 * SR)] *= np.linspace(0, 1, int(0.015 * SR))
    return ir / (np.max(np.abs(ir)) + 1e-9)


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as f:
        data = np.frombuffer(f.readframes(f.getnframes()), dtype="<i2").astype(np.float32) / 32768
        return data.reshape(-1, f.getnchannels()).T


def write_wav(path: Path, wav: np.ndarray):
    data = np.clip(wav.T, -1, 1)
    with wave.open(str(path), "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes((data * 32767).astype("<i2").tobytes())


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    meta = json.loads((PROJ / "timing.json").read_text(encoding="utf-8"))
    lines = meta["lines"]
    duration = float(meta["duration"])
    starts = [l["start"] for l in lines]

    # boundaries: hook, question, answer, light, distance, sync, line, outro
    bounds = [0.0, starts[2], starts[4], starts[5], starts[9], starts[12], starts[15], starts[18], duration]
    labels = ["hook", "question", "answer", "light", "distance", "sync", "line", "outro"]
    print("bounds", [round(b, 2) for b in bounds])

    music = compose(duration, bounds, labels)
    write_wav(PROJ / "music.wav", music)

    voice = read_wav(PROJ / "voice.wav")
    if voice.shape[1] < music.shape[1]:
        voice = np.pad(voice, ((0, 0), (0, music.shape[1] - voice.shape[1])))
    else:
        voice = voice[:, : music.shape[1]]

    # duck the score under the voice
    mono = voice.mean(axis=0)
    k = int(0.06 * SR)
    env = np.convolve(np.abs(mono), np.ones(k) / k, mode="same")
    env = env / (env.max() + 1e-9)
    duck = 1.0 - 0.64 * np.clip(env * 3.4, 0, 1)
    music_d = music * duck

    mix = voice * 1.5 + music_d * 0.38
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    mix = normalize(mix, 0.9)
    write_wav(PROJ / "mix.wav", mix)

    out = {
        "title": "未见面的缘分",
        "bpm": BPM,
        "beat_seconds": round(BEAT, 4),
        "duration": duration,
        "sections": [
            {"label": labels[i], "start": round(bounds[i], 3), "end": round(bounds[i + 1], 3)}
            for i in range(len(labels))
        ],
        "voice": {"file": "voice.wav", "sha256": sha256(PROJ / "voice.wav"), "lines": len(lines)},
        "music": {"file": "music.wav", "sha256": sha256(PROJ / "music.wav")},
        "mix": {"file": "mix.wav", "sha256": sha256(PROJ / "mix.wav")},
        "generator": "engine/yuanfen_audio.py (numpy, no samples)",
    }
    (PROJ / "audio.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"music {duration:.2f}s -> {PROJ / 'music.wav'}; mix -> {PROJ / 'mix.wav'}")


if __name__ == "__main__":
    main()
