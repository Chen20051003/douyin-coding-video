param(
  [string]$RepoName = "douyin-coding-video",
  [switch]$Private
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$portableGit = Join-Path $root "tools\git\cmd"
if (Test-Path (Join-Path $portableGit "git.exe")) { $env:PATH = "$portableGit;$env:PATH" }
Set-Location $root

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Write-Host "ERROR: Git not installed. Install Git for Windows first." -ForegroundColor Red
  exit 2
}
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
  Write-Host "ERROR: GitHub CLI (gh) not installed." -ForegroundColor Red
  exit 2
}
gh auth status 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) {
  Write-Host "ERROR: gh not logged in. Run: gh auth login" -ForegroundColor Red
  exit 3
}

if (-not (Test-Path ".git")) {
  git init -b main
  git add -A
  git -c user.name="douyin-coding-video" -c user.email="noreply@local" commit -m "feat: four code-generated Douyin videos + skill pipeline"
}
$visibility = if ($Private) { "--private" } else { "--public" }
$existing = git remote 2>$null
if ($existing -notcontains "origin") {
  gh repo create $RepoName $visibility --source . --remote origin --push
} else {
  git push -u origin main
}
Write-Host "done: https://github.com/$(gh api user -q .login)/$RepoName"
