"""Deterministic numpy audio synthesis for the three Douyin-style videos.

No external samples, no model weights: every sound is generated here, so the
track identity is provable from source + score, not from a waveform guess.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

SR = 44100
ROOT = Path(__file__).resolve().parents[1]
RNG = np.random.default_rng(20261020)


# ---------------------------------------------------------------- primitives
def sec(d: float) -> int:
    return int(round(d * SR))


def midi(n: float) -> float:
    return 440.0 * 2 ** ((n - 69) / 12)


def adsr(n: int, a=0.01, d=0.08, s=0.7, r=0.2) -> np.ndarray:
    a_n, d_n, r_n = max(1, sec(a)), max(1, sec(d)), max(1, sec(r))
    env = np.ones(n)
    a_n = min(a_n, n)
    env[:a_n] = np.linspace(0, 1, a_n)
    d_end = min(a_n + d_n, n)
    env[a_n:d_end] = np.linspace(1, s, d_end - a_n)
    env[d_end:] = s
    if r_n < n:
        env[-r_n:] *= np.linspace(1, 0, r_n)
    return env


def saw(freq: float, n: int, phase: float = 0.0) -> np.ndarray:
    t = np.arange(n) / SR
    return 2.0 * ((freq * t + phase) % 1.0) - 1.0


def sine(freq: float, n: int, phase: float = 0.0) -> np.ndarray:
    return np.sin(2 * np.pi * freq * np.arange(n) / SR + phase)


def lowpass(x: np.ndarray, fc: float, order: int = 2) -> np.ndarray:
    fc = min(fc, SR * 0.45)
    sos = butter(order, fc / (SR / 2), btype="low", output="sos")
    return sosfilt(sos, x)


def highpass(x: np.ndarray, fc: float, order: int = 2) -> np.ndarray:
    sos = butter(order, max(20, fc) / (SR / 2), btype="high", output="sos")
    return sosfilt(sos, x)


def normalize(x: np.ndarray, peak: float = 0.9) -> np.ndarray:
    m = float(np.max(np.abs(x))) if x.size else 0.0
    return x * (peak / m) if m > 1e-9 else x


def place(buf: np.ndarray, sig: np.ndarray, start: float, pan: float = 0.0, gain: float = 1.0):
    i = sec(start)
    if i >= buf.shape[1]:
        return
    n = min(len(sig), buf.shape[1] - i)
    if n <= 0:
        return
    l = np.cos((pan + 1) * np.pi / 4)
    r = np.sin((pan + 1) * np.pi / 4)
    buf[0, i : i + n] += sig[:n] * gain * l
    buf[1, i : i + n] += sig[:n] * gain * r


def make_ir(decay: float = 1.6, length: float = 2.4, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = sec(length)
    t = np.arange(n) / SR
    ir = rng.normal(0, 1, n) * np.exp(-t / decay)
    ir = lowpass(ir, 5200)
    ir[: sec(0.012)] *= np.linspace(0, 1, sec(0.012))
    return ir / (np.max(np.abs(ir)) + 1e-9)


def reverb(x: np.ndarray, wet: float = 0.28, decay: float = 1.6, length: float = 2.4) -> np.ndarray:
    ir = make_ir(decay, length)
    w = fftconvolve(x, ir, mode="full")[: len(x)]
    w = normalize(w, 1.0)
    return (1 - wet) * x + wet * w


def sidechain(n: int, kicks: list[float], depth: float = 0.55, tau: float = 0.13) -> np.ndarray:
    env = np.ones(n)
    for k in kicks:
        i = sec(k)
        if i >= n:
            break
        idx = np.arange(i, min(i + sec(0.45), n))
        tt = (idx - i) / SR
        env[idx] = np.minimum(env[idx], 1 - depth * np.exp(-tt / tau))
    return env


# ------------------------------------------------------------------- voices
def piano(freq: float, dur: float, vel: float = 0.8) -> np.ndarray:
    n = sec(dur)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for h, amp, dec, det in (
        (1, 1.00, 1.9, 0.0),
        (2, 0.46, 1.15, 0.6),
        (3, 0.24, 0.75, -0.4),
        (4, 0.12, 0.50, 0.3),
        (5, 0.06, 0.36, -0.2),
        (6, 0.03, 0.26, 0.1),
    ):
        out += amp * np.sin(2 * np.pi * (freq * h + det) * t + h * 0.7) * np.exp(-t / dec)
    out *= 1 - np.exp(-t / 0.004)
    noise = RNG.normal(0, 1, n) * np.exp(-t / 0.018) * 0.03
    out = normalize(out, 1.0) * vel + noise
    return out * adsr(n, 0.004, 0.05, 0.85, min(0.5, dur * 0.4))


def pad_chord(freqs: list[float], dur: float, cutoff: float = 1500.0) -> np.ndarray:
    n = sec(dur)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for f in freqs:
        for det in (-0.006, -0.002, 0.002, 0.006):
            out += saw(f * (1 + det), n, phase=float(RNG.random()))
    out = lowpass(out, cutoff, 2)
    env = np.minimum(t / 1.4, 1.0) * np.minimum((dur - t) / 1.8, 1.0)
    return normalize(out * env, 1.0)


def string_low(freq: float, dur: float) -> np.ndarray:
    n = sec(dur)
    out = saw(freq, n) + 0.5 * saw(freq * 1.005, n, 0.2)
    out = lowpass(out, 420, 2)
    return normalize(out, 1.0) * adsr(n, 0.6, 0.2, 0.8, min(0.9, dur * 0.4))


def bass_note(freq: float, dur: float, bright: float = 260.0) -> np.ndarray:
    n = sec(dur)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * freq * t) + 0.35 * saw(freq, n)
    body = lowpass(body, bright, 2)
    body *= np.exp(-t / 0.22)
    return normalize(body, 1.0) * adsr(n, 0.005, 0.04, 0.9, 0.08)


def pluck(freq: float, dur: float = 0.32, bright: float = 2600.0) -> np.ndarray:
    n = sec(dur)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for h in range(1, 6):
        out += (1 / h) * np.sin(2 * np.pi * freq * h * t) * np.exp(-t / (0.22 / h))
    out = lowpass(out, bright)
    return normalize(out, 1.0) * (1 - np.exp(-t / 0.003))


def kick(dur: float = 0.42, f0: float = 140.0, f1: float = 44.0, punch: float = 1.0) -> np.ndarray:
    n = sec(dur)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t / 0.028)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.17)
    click = RNG.normal(0, 1, n) * np.exp(-t / 0.004) * 0.25
    return np.tanh((body + click) * 1.6 * punch)


def snare(dur: float = 0.24, tone: float = 185.0) -> np.ndarray:
    n = sec(dur)
    t = np.arange(n) / SR
    noise = RNG.normal(0, 1, n)
    noise = highpass(noise, 1100) * np.exp(-t / 0.07)
    body = np.sin(2 * np.pi * tone * t) * np.exp(-t / 0.05) * 0.5
    return np.tanh((noise * 1.1 + body) * 1.2)


def hat(dur: float = 0.055, open_: bool = False) -> np.ndarray:
    n = sec(0.18 if open_ else dur)
    t = np.arange(n) / SR
    noise = highpass(RNG.normal(0, 1, n), 7000)
    return noise * np.exp(-t / (0.09 if open_ else 0.018)) * 0.5


def riser(dur: float) -> np.ndarray:
    n = sec(dur)
    t = np.arange(n) / SR
    noise = RNG.normal(0, 1, n)
    # sweeping band emphasis by crossfading two filtered noises
    lo = lowpass(noise, 500)
    hi = highpass(noise, 2500)
    mix = np.linspace(0, 1, n) ** 2
    out = lo * (1 - mix) + hi * mix
    return normalize(out * (t / dur) ** 1.5, 1.0)


def boom(dur: float = 1.2, f: float = 46.0) -> np.ndarray:
    n = sec(dur)
    t = np.arange(n) / SR
    sig = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.45)
    return np.tanh(sig * 1.4)


# ------------------------------------------------------------------ mixing
@dataclass
class Track:
    bpm: int
    key: str
    duration: float
    sections: list[tuple[float, float, str]]
    chords: list[str]


def finish(dry: np.ndarray, wet: np.ndarray, wet_mix: float, name: str, fade_in: float = 0.6, fade_out: float = 2.0) -> np.ndarray:
    w = np.zeros_like(dry)
    for ch in range(2):
        w[ch] = fftconvolve(wet[ch], make_ir(1.7, 2.6, 11), mode="full")[: dry.shape[1]]
    w = normalize(w, 1.0)
    mix = dry + w * wet_mix
    mix = np.tanh(mix * 1.15) / np.tanh(1.15)
    n = mix.shape[1]
    env = np.ones(n)
    fi, fo = min(sec(fade_in), n), min(sec(fade_out), n)
    if fi:
        env[:fi] = np.linspace(0, 1, fi) ** 0.6
    if fo:
        env[-fo:] *= np.linspace(1, 0, fo) ** 1.3
    mix *= env
    return normalize(mix, 0.84)


# -------------------------------------------------------------- knowledge BGM
def compose_knowledge(dur: float = 126.0) -> tuple[np.ndarray, Track]:
    bpm = 77
    beat = 60 / bpm
    bar = beat * 4
    n = sec(dur)
    dry = np.zeros((2, n))
    wet = np.zeros((2, n))

    prog = [
        ("Am", [220.00, 261.63, 329.63, 440.00], 110.00),
        ("F", [174.61, 220.00, 261.63, 349.23], 87.31),
        ("C", [261.63, 329.63, 392.00, 523.25], 130.81),
        ("G", [196.00, 246.94, 293.66, 392.00], 98.00),
    ]
    sections = [
        (0, 18, "hook-pad"),
        (18, 50, "history-piano"),
        (50, 64, "index"),
        (64, 78, "generation"),
        (78, 96, "memory"),
        (96, 110, "judgment"),
        (110, 126, "outro"),
    ]

    def w_at(t: float, piano_w: float, arp_w: float, drum_w: float):
        # smooth 1.2s fades at section boundaries
        fade = 1.0
        for s, _ in sections[1:]:
            fade *= min(1.0, max(0.0, abs(t - s) / 1.2))
        return fade

    bars = int(np.ceil(dur / bar))
    for b in range(bars):
        t0 = b * bar
        if t0 >= dur:
            break
        name, tones, root = prog[b % 4]
        # pad
        pad = pad_chord(tones, min(bar + 0.4, dur - t0), 1400)
        place(dry, pad, t0, 0.0, 0.095)
        place(wet, pad, t0, 0.0, 0.10)
        # low strings
        st = string_low(root / 2, min(bar, dur - t0))
        place(dry, st, t0, -0.15, 0.055)
        place(wet, st, t0, -0.15, 0.05)
        # piano arpeggio (8th notes)
        if t0 >= 18:
            pattern = [0, 2, 1, 3, 2, 1, 3, 2]
            for i, p in enumerate(pattern):
                tt = t0 + i * beat / 2
                if tt >= dur:
                    break
                f = tones[p] * (2 if (i in (3, 6)) else 1)
                note = piano(f, min(2.6, dur - tt), 0.72)
                g = 0.115 if tt < 50 else 0.14
                if tt >= 96:
                    g = 0.10
                if tt >= 110:
                    g = 0.085
                place(dry, note, tt, -0.2 if i % 2 else 0.18, g * 1.25)
                place(wet, note, tt, 0.0, g * 1.5)
        # bass
        if t0 >= 18:
            for k in (0, 2):
                tt = t0 + k * beat
                if tt >= dur:
                    break
                place(dry, bass_note(root / 2, beat * 1.7), tt, 0.0, 0.075)
        # soft drums from generation section
        if 64 <= t0 < 96:
            for k in (0, 2):
                tt = t0 + k * beat
                if tt >= dur:
                    break
                place(dry, kick(0.35, 110, 48), tt, 0.0, 0.10)
            for i in range(4):
                tt = t0 + i * beat / 2 + beat / 4
                if tt < dur:
                    place(dry, hat(0.04), tt, 0.25, 0.012)

    # sparse piano motif in hook & outro
    for tt, f in ((3.0, 440.0), (7.8, 392.0), (12.4, 329.63), (115.0, 440.0), (119.5, 523.25)):
        if tt < dur:
            place(dry, piano(f, 4.0, 0.6), tt, 0.0, 0.06)
            place(wet, piano(f, 4.0, 0.6), tt, 0.0, 0.15)

    # air
    hiss = lowpass(RNG.normal(0, 1, n), 900) * 0.004
    dry += hiss

    out = finish(dry, wet, 0.42, "knowledge", 1.2, 4.0)
    return out, Track(bpm, "A minor", dur, sections, [p[0] for p in prog])


# ------------------------------------------------------------------ 128 BPM beat
def compose_beat(dur: float = 24.0) -> tuple[np.ndarray, Track]:
    bpm = 128
    beat = 60 / bpm
    bar = beat * 4
    n = sec(dur)
    dry = np.zeros((2, n))
    wet = np.zeros((2, n))

    prog = [
        ("Fm", [174.61, 207.65, 261.63], 87.31),
        ("Db", [138.59, 174.61, 207.65], 69.30),
        ("Ab", [207.65, 261.63, 311.13], 103.83),
        ("Eb", [155.56, 196.00, 233.08], 77.78),
    ]
    sections = [
        (0.0, 3.75, "intro"),
        (3.75, 7.5, "prompt"),
        (7.5, 11.25, "code"),
        (11.25, 15.0, "test"),
        (15.0, 18.75, "build"),
        (18.75, 22.5, "deploy"),
        (22.5, 24.0, "outro"),
    ]
    kicks = []
    for i in range(int(22.5 / beat) + 1):
        tt = i * beat
        if tt >= dur:
            break
        kicks.append(tt)
        place(dry, kick(0.4), tt, 0.0, 0.55)
    for i, k in enumerate(kicks):
        if i % 4 in (1, 3):
            place(dry, snare(), k, 0.05, 0.34)
            place(wet, snare(), k, 0.05, 0.18)
    # hats
    t = 0.0
    while t < 22.5:
        place(dry, hat(0.035), t, 0.3, 0.09)
        if abs((t / beat) % 1 - 0.5) < 1e-6:
            place(dry, hat(0.05, open_=True), t, -0.25, 0.05)
        t += beat / 2

    # bass / pad / arp per bar
    for b in range(int(np.ceil(dur / bar))):
        t0 = b * bar
        if t0 >= dur:
            break
        name, tones, root = prog[b % 4]
        pad = pad_chord(tones, min(bar, dur - t0), 2100)
        sc = sidechain(n, kicks, 0.6, 0.11)
        pad = pad * sc[sec(t0) : sec(t0) + len(pad)]
        place(dry, pad, t0, 0.0, 0.13)
        place(wet, pad, t0, 0.0, 0.08)
        for i in range(8):
            tt = t0 + i * beat / 2
            if tt >= dur or tt >= 22.5:
                break
            f = root * (2 if i in (3, 6) else 1)
            place(dry, bass_note(f, beat * 0.42, 220), tt, 0.0, 0.26)
        if t0 >= 7.5:
            for i in range(16):
                tt = t0 + i * beat / 4
                if tt >= dur or tt >= 21.5:
                    break
                f = tones[(i * 3 + b) % len(tones)] * 2
                place(dry, pluck(f, 0.22), tt, -0.3 if i % 2 else 0.3, 0.075)
                place(wet, pluck(f, 0.22), tt, 0.0, 0.05)

    place(dry, riser(1.875), 9.375, 0.0, 0.22)
    place(dry, riser(1.875), 18.75, 0.0, 0.18)
    place(dry, boom(1.6), 11.25, 0.0, 0.55)
    place(dry, boom(1.6), 20.625, 0.0, 0.45)

    out = finish(dry, wet, 0.22, "beat", 0.15, 0.8)
    return out, Track(bpm, "F minor", dur, sections, [p[0] for p in prog])


# ------------------------------------------------------------------ 96 BPM music
def compose_music(dur: float = 30.0) -> tuple[np.ndarray, Track]:
    bpm = 96
    beat = 60 / bpm
    bar = beat * 4
    n = sec(dur)
    dry = np.zeros((2, n))
    wet = np.zeros((2, n))

    prog = [
        ("C#m", [277.18, 329.63, 415.30], 69.30),
        ("A", [220.00, 277.18, 329.63], 55.00),
        ("E", [246.94, 329.63, 415.30], 82.41),
        ("B", [246.94, 311.13, 369.99], 61.74),
    ]
    sections = [
        (0.0, 6.0, "intro"),
        (6.0, 12.0, "build"),
        (12.0, 15.0, "riser"),
        (15.0, 24.0, "drop"),
        (24.0, 30.0, "outro"),
    ]
    kicks = []
    for i in range(int(24.0 / beat) + 1):
        tt = i * beat
        if tt < 24.0:
            kicks.append(tt)
            if tt >= 6.0:
                place(dry, kick(0.38, 120, 42), tt, 0.0, 0.5)
    for k in kicks:
        if k >= 15.0 and (round(k / beat) % 4 in (1, 3)):
            place(dry, snare(0.28, 200), k, 0.0, 0.28)
            place(wet, snare(0.28, 200), k, 0.0, 0.2)
    t = 6.0
    while t < 24.0:
        place(dry, hat(0.03), t, 0.35, 0.055)
        t += beat / 4

    for b in range(int(np.ceil(dur / bar))):
        t0 = b * bar
        if t0 >= dur:
            break
        name, tones, root = prog[b % 4]
        pad = pad_chord([f * 2 for f in tones], min(bar + 0.5, dur - t0), 2400)
        sc = sidechain(n, kicks, 0.62, 0.14)
        pad = pad * sc[sec(t0) : sec(t0) + len(pad)]
        place(dry, pad, t0, 0.0, 0.12)
        place(wet, pad, t0, 0.0, 0.12)
        for i in range(8):
            tt = t0 + i * beat / 2
            if tt >= dur:
                break
            place(dry, bass_note(root, beat * 0.46, 140), tt, 0.0, 0.24)
        for i in range(16):
            tt = t0 + i * beat / 4
            if tt >= dur:
                break
            f = tones[(i * 2 + b) % len(tones)] * 4
            place(dry, pluck(f, 0.18, 4200), tt, -0.35 if i % 2 else 0.35, 0.045)
            place(wet, pluck(f, 0.18, 4200), tt, 0.0, 0.06)

    # lead motif in the drop
    motif = [(15.0, 0, 1.0), (15.625, 4, 0.8), (16.25, 7, 0.9), (16.875, 4, 0.7),
             (17.5, 0, 1.0), (18.125, 2, 0.8), (18.75, 4, 0.9), (19.375, 7, 0.8),
             (20.0, 9, 0.9), (20.625, 7, 0.8), (21.25, 4, 0.9), (21.875, 2, 0.7)]
    scale = [0, 2, 3, 5, 7, 8, 10, 12, 14, 15]
    for tt, deg, g in motif:
        if tt + 0.5 >= dur:
            continue
        f = 277.18 * 2 ** (scale[deg % len(scale)] / 12)
        note = pluck(f, 0.55, 5000) * 0.6 + sine(f, sec(0.55)) * 0.4
        place(dry, note, tt, 0.0, 0.055 * g)
        place(wet, note, tt, 0.0, 0.09)

    place(dry, riser(3.0), 12.0, 0.0, 0.20)
    place(dry, boom(1.8), 15.0, 0.0, 0.45)
    place(dry, boom(1.4), 24.0, 0.0, 0.25)

    out = finish(dry, wet, 0.5, "music", 0.8, 2.5)
    return out, Track(bpm, "C# minor", dur, sections, [p[0] for p in prog])


# ------------------------------------------------------------------ analysis
def spectrum_frames(wav: np.ndarray, fps: int = 30, bands: int = 64) -> dict:
    mono = wav.mean(axis=0)
    win = 2048
    hop = SR // fps
    total = int(len(mono) / SR * fps)
    edges = np.geomspace(35, 16000, bands + 1)
    frames = []
    for i in range(total):
        c = i * hop
        seg = mono[max(0, c - win // 2) : c + win // 2]
        if len(seg) < win:
            seg = np.pad(seg, (0, win - len(seg)))
        spec = np.abs(np.fft.rfft(seg * np.hanning(win)))
        freqs = np.fft.rfftfreq(win, 1 / SR)
        vals = []
        for b in range(bands):
            m = (freqs >= edges[b]) & (freqs < edges[b + 1])
            vals.append(float(spec[m].mean()) if m.any() else 0.0)
        frames.append(vals)
    arr = np.array(frames)
    arr = arr / (np.percentile(arr, 98) + 1e-9)
    arr = np.clip(arr, 0, 1) ** 0.65
    return {"fps": fps, "bands": bands, "frames": arr.round(4).tolist()}


def waveform_points(wav: np.ndarray, points: int = 1600) -> list[float]:
    mono = wav.mean(axis=0)
    chunk = max(1, len(mono) // points)
    vals = [float(np.max(np.abs(mono[i : i + chunk]))) for i in range(0, len(mono), chunk)]
    vals = np.array(vals)
    vals = vals / (vals.max() + 1e-9)
    return vals.round(4).tolist()


def write_wav(path: Path, wav: np.ndarray):
    data = np.clip(wav.T, -1, 1)
    pcm = (data * 32767).astype("<i2")
    with wave.open(str(path), "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(pcm.tobytes())


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


TRACKS = {
    "knowledge": (compose_knowledge, 126.0, -14.0),
    "beat": (compose_beat, 24.0, -12.0),
    "music": (compose_music, 30.0, -12.0),
}


def build(name: str, out_root: Path):
    fn, dur, target = TRACKS[name]
    wav, track = fn(dur)
    out = out_root / name
    out.mkdir(parents=True, exist_ok=True)
    wav_path = out / "audio.wav"
    write_wav(wav_path, wav)

    meta = {
        "name": name,
        "bpm": track.bpm,
        "key": track.key,
        "duration": track.duration,
        "sections": [{"start": a, "end": b, "label": c} for a, b, c in track.sections],
        "progression": track.chords,
        "target_lufs": target,
        "sample_rate": SR,
        "sha256": sha256(wav_path),
        "generator": "engine/audio.py (numpy synthesis, no samples)",
        "peak_dbfs": round(float(20 * np.log10(np.max(np.abs(wav)) + 1e-9)), 2),
    }
    beat = 60 / track.bpm
    meta["beat_seconds"] = round(beat, 6)
    meta["beats"] = [round(i * beat, 4) for i in range(int(track.duration / beat))]

    if name == "music":
        spec = spectrum_frames(wav, 30, 64)
        (out / "spectrum.js").write_text(
            "window.SPECTRUM=" + json.dumps(spec, separators=(",", ":")) + ";\n", encoding="utf-8"
        )
        meta["spectrum"] = {"fps": spec["fps"], "bands": spec["bands"], "frames": len(spec["frames"])}
        (out / "waveform.js").write_text(
            "window.WAVEFORM=" + json.dumps(waveform_points(wav)) + ";\n", encoding="utf-8"
        )

    (out / "audio.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{name}] {track.duration}s {track.bpm}BPM {track.key} peak={meta['peak_dbfs']}dBFS -> {wav_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--track", default="all", choices=["all", *TRACKS])
    ap.add_argument("--out", default=str(ROOT / "projects"))
    args = ap.parse_args()
    out = Path(args.out)
    names = list(TRACKS) if args.track == "all" else [args.track]
    for name in names:
        build(name, out)


if __name__ == "__main__":
    main()
