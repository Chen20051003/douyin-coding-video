param([string]$Name = "douyin-coding-video")
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$target = Join-Path $HOME ".agents\skills\$Name"
Write-Host "install skill: $root -> $target"
robocopy $root $target /E /XD out qa research .git node_modules __pycache__ /XF *.mp4 *.wav | Out-Host
if ($LASTEXITCODE -ge 8) { throw "robocopy failed with $LASTEXITCODE" }
Write-Host "OK. Read $target\SKILL.md"
