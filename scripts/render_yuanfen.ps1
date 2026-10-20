param()
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

python engine/tts.py
python engine/yuanfen_audio.py
python engine/capture.py --html projects/yuanfen/index.html `
  --out out/yuanfen/frames --width 1920 --height 1080 --duration 79.53 --fps 30
python engine/encode.py --frames out/yuanfen/frames `
  --audio projects/yuanfen/mix.wav --out out/yuanfen.mp4 --lufs -14
python engine/video_qa.py --file out/yuanfen.mp4 --out qa/final/yuanfen
Write-Host "done: out/yuanfen.mp4"
