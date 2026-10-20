# 部署到 GitHub

## 当前状态（2026-10-20）

- `gh auth status` → **未登录**（设备码流程已发起，等待授权）
- Git → 已放置便携版 `tools\git`（2.55.0）；`deploy_github.ps1` 会自动把它加入 PATH
- 因此本机**尚未执行** `git push`，GitHub 上暂时没有这个仓库。
- 仓库结构、`.gitignore`、GitHub Actions、部署脚本均已就绪。

## 一次性准备

1. 登录 GitHub CLI：

```powershell
gh auth login
```

2. 回到仓库根目录，执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/deploy_github.ps1
```

脚本会：

- 检查 `git` / `gh` / 登录状态
- `git init -b main` + 首次提交
- `gh repo create douyin-coding-video --public --source . --push`

指定私有仓库：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/deploy_github.ps1 -Private
```

## 手动方式

```powershell
git init -b main
git add -A
git commit -m "feat: three code-generated Douyin videos + skill pipeline"
gh repo create douyin-coding-video --public --source . --remote origin --push
```

## 仓库不会包含

`.gitignore` 已排除：

- `out/`（成片与帧序列）
- `qa/`（质检截图）
- `assets/fonts/`（约 40MB 字体）
- `projects/*/audio.wav`（可由 `engine/audio.py` 重新生成）

克隆后先运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/fetch_fonts.ps1
python engine/audio.py --track all
```

## 本地技能安装

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install.ps1
```

安装到 `~/.agents/skills/douyin-coding-video`，Agent 读取其中的 `SKILL.md`。
