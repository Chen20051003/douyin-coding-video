# AGENTS.md

本仓库是一个可安装的 Agent Skill，也是一套可直接运行的视频工程。

## 先读

1. `SKILL.md` — 三条配方、七步流水线、硬规则。
2. `references/style-dna.md` — 实测版式与音频参数。
3. `references/qa-checklist.md` — 交付前必过项。

## 运行约定

- 只改 `projects/*/index.html`、`engine/*`、`scripts/*`；不要改 `qa/` 与 `out/` 里的成片。
- 所有动画必须是 `render(t)` 的纯函数；禁止 `Date.now()`、`Math.random()`、CSS 动画。
- 重新渲染前先渲关键静帧目检。
- 成片只认 `out/*.mp4`；浏览器截图不算交付。
- 不提交 `out/`、`qa/`、`assets/fonts/`、`projects/*/audio.wav`。

## 常用命令

```powershell
python engine/audio.py --track all
python engine/capture.py --html projects/knowledge/index.html --out qa/stills/knowledge --width 1920 --height 1080 --duration 126 --still 17,60,90
python engine/capture.py --html projects/knowledge/index.html --out out/knowledge/frames --width 1920 --height 1080 --duration 126 --fps 30
python engine/encode.py --frames out/knowledge/frames --audio projects/knowledge/audio.wav --out out/knowledge.mp4 --lufs -14
python engine/video_qa.py --file out/knowledge.mp4 --out qa/final/knowledge
```

## 边界

- 不下载第三方视频/音乐素材。
- 不伪造抖音热度、播放量、排名或产品截图。
- 引用公开文档并标日期；界面标「示意」。
