param()
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$dst = Join-Path $root "assets\fonts"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
$pairs = @(
  @{ src = "C:\Windows\Fonts\NotoSansSC-VF.ttf";  name = "NotoSansSC-VF.ttf" },
  @{ src = "C:\Windows\Fonts\NotoSerifSC-VF.ttf"; name = "NotoSerifSC-VF.ttf" }
)
foreach ($p in $pairs) {
  if (Test-Path $p.src) {
    Copy-Item $p.src (Join-Path $dst $p.name) -Force
    Write-Host "OK  $($p.name)"
  } else {
    Write-Warning "missing $($p.src) — install Noto Sans SC / Noto Serif SC or copy a variable font manually"
  }
}
Write-Host "fonts -> $dst"
