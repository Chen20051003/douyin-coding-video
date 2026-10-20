"""Lightweight repo validation; no browser or ffmpeg required."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {"knowledge": (77, 126.0), "beat": (128, 24.0), "music": (96, 30.0), "yuanfen": (112, 86.15)}
errors = []

for name, (bpm, dur) in EXPECTED.items():
    p = ROOT / "projects" / name
    html = p / "index.html"
    if not html.exists():
        errors.append(f"{name}: missing index.html")
        continue
    text = html.read_text(encoding="utf-8")
    for token in ("window.render", "window.__ready", "render(t)"):
        if token not in text:
            errors.append(f"{name}: index.html missing {token}")
    meta = p / "audio.json"
    if not meta.exists():
        errors.append(f"{name}: missing audio.json")
        continue
    data = json.loads(meta.read_text(encoding="utf-8"))
    if data.get("bpm") != bpm:
        errors.append(f"{name}: bpm {data.get('bpm')} != {bpm}")
    if abs(float(data.get("duration", 0)) - dur) > 0.01:
        errors.append(f"{name}: duration {data.get('duration')} != {dur}")
    sha = data.get("mix", {}).get("sha256", "") if name == "yuanfen" else data.get("sha256", "")
    if len(sha) != 64:
        errors.append(f"{name}: bad sha256")

if not (ROOT / "projects" / "music" / "spectrum.js").exists():
    errors.append("music: missing spectrum.js (run engine/audio.py)")
if not (ROOT / "assets" / "fonts").exists():
    print("warn: assets/fonts missing; run scripts/fetch_fonts.ps1 before rendering")

print(json.dumps({"projects": list(EXPECTED), "errors": errors}, ensure_ascii=False, indent=2))
sys.exit(1 if errors else 0)
