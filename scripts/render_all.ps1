param(
  [ValidateSet("all", "knowledge", "beat", "music")]
  [string]$Only = "all"
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

python engine/audio.py --track all
python engine/audio_qa.py

$jobs = @(
  @{ name = "knowledge"; w = 1920; h = 1080; dur = 126; lufs = -14 },
  @{ name = "beat";      w = 1080; h = 1920; dur = 24;  lufs = -12 },
  @{ name = "music";     w = 1080; h = 1920; dur = 30;  lufs = -12 }
)
foreach ($j in $jobs) {
  if ($Only -ne "all" -and $Only -ne $j.name) { continue }
  Write-Host "=== $($j.name) ==="
  python engine/capture.py --html "projects/$($j.name)/index.html" `
    --out "out/$($j.name)/frames" --width $j.w --height $j.h --duration $j.dur --fps 30
  python engine/encode.py --frames "out/$($j.name)/frames" `
    --audio "projects/$($j.name)/audio.wav" --out "out/$($j.name).mp4" --fps 30 --lufs $j.lufs
  python engine/video_qa.py --file "out/$($j.name).mp4" --out "qa/final/$($j.name)"
}
Write-Host "done"
