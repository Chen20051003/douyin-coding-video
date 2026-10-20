import sys, wave, json, numpy as np
from pathlib import Path
sys.path.insert(0, "engine")
from audio import SR, riser, boom, kick, normalize

P = Path("projects/nihilism")
tim = json.loads((P / "timing.json").read_text(encoding="utf-8"))
DROP = tim["lines"][17]["start"]
HIT = tim["lines"][4]["start"]


def read(p):
    with wave.open(str(p), "rb") as f:
        a = np.frombuffer(f.readframes(f.getnframes()), dtype="<i2").astype(np.float32) / 32768
        return a.reshape(-1, f.getnchannels()).T


def write(p, x):
    with wave.open(str(p), "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes((np.clip(x.T, -1, 1) * 32767).astype("<i2").tobytes())


def add(buf, sig, t, g=1.0):
    i = int(t * SR)
    n = min(len(sig), buf.shape[1] - i)
    if n > 0:
        buf[:, i:i + n] += sig[:n] * g


v = read(P / "voice.wav")
b = read(P / "bgm_ref.wav")
n = v.shape[1]
b = b[:, :n]
if b.shape[1] < n:
    b = np.pad(b, ((0, 0), (0, n - b.shape[1])))

# duck curve into the drop
gain = np.ones(n, float)


def ramp(a, bb, ga, gb):
    i0, i1 = int(a * SR), int(bb * SR)
    if i1 > i0:
        gain[i0:i1] = np.linspace(ga, gb, i1 - i0)


ramp(68.6, 69.6, 1.0, 0.58)
ramp(69.6, 70.55, 0.58, 0.26)
ramp(70.55, DROP, 0.26, 0.02)
gain[int(DROP * SR):int((DROP + 0.8) * SR)] = 1.0

# SFX
sfx = np.zeros((2, n))
add(sfx, riser(1.45), 69.0, 0.38)
for t, g in ((69.0, .25), (69.45, .32), (69.85, .40), (70.2, .48), (70.35, .55)):
    add(sfx, kick(.32, 95, 46), t, g)
add(sfx, boom(1.6, 42), DROP, 0.95)
add(sfx, riser(.35), DROP, 0.5)
add(sfx, boom(.85, 55), HIT, 0.6)
# paper slam at HIT
nn = int(.35 * SR)
tt = np.arange(nn) / SR
slap = np.random.default_rng(4).normal(0, 1, nn) * np.exp(-tt / .06) * 0.35
add(sfx, slap, HIT, 1.0)

# vacuum: 0.28s of near-silence right before the drop
vac = np.ones(n)
i0, i1 = int(70.45 * SR), int(70.88 * SR)
vac[i0:i1] = 0.0
j0, j1 = int(70.45 * SR), int(70.60 * SR)
vac[j0:j1] = np.linspace(1, 0, j1 - j0)
b = b * vac[None, :]
sfx = sfx * vac[None, :]

# voice + bgm + sfx
mix = v * 1.12 + b * 0.62 * gain + sfx * 0.9
mix = np.tanh(mix * 1.05) / np.tanh(1.05)
mix = normalize(mix, 0.92)
write(P / "mix_v2_voice.wav", mix)

# no voice
mix2 = b * 0.75 * gain + sfx * 0.95
mix2 = np.tanh(mix2 * 1.05) / np.tanh(1.05)
mix2 = normalize(mix2, 0.92)
write(P / "mix_v2_novoice.wav", mix2)
print("DROP", DROP, "HIT", HIT, "dur", n / SR)
