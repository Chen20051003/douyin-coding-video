# 抖音短视频 · 四条成片 + 可复用技能

> 目标：把「抖音上最火的编程软件」与「未见面的缘分」做成四条可直接发布的代码生成视频——
> **知识大赏横屏**、**128 BPM 卡点竖屏**、**96 BPM AI 音乐可视化竖屏**、**104 BPM 配音情感短片**。
> 同时把方法论封装成 Agent Skill，并准备一键部署到 GitHub。

## 交付物

| # | 成片 | 规格 | 内容 |
|---|---|---|---|
| 01 | `out/01_知识大赏_快是被设计出来的.mp4` | 1920×1080 / 30fps / 126s | 逆向拆解 AI 编程软件的三层加速：索引、生成、上下文内存 |
| 02 | `out/02_卡点_VIBE_CODING_128BPM.mp4` | 1080×1920 / 30fps / 24s | 一句话 → 生成 → 测试 → 构建 → 上线，每 2 拍一刀 |
| 03 | `out/03_AI音乐_代码合成.mp4` | 1080×1920 / 30fps / 30s | 64 段频谱驱动的 AI 音乐可视化，drop 对齐 15s |
| 04 | `out/04_未见面的缘分.mp4` | 1920×1080 / 30fps / 73.84s | 104BPM 太鼓 + 中文 AI 配音，关于屏幕两端的友谊 |

每条片子都包含：`index.html` 源码、`audio.wav` 合成音轨、`audio.json` 乐谱元数据、`qa.json` 技术质检、关键帧截图。

## 快速开始

```powershell
# 1) 字体（仓库不提交 40MB 字体）
powershell -ExecutionPolicy Bypass -File scripts/fetch_fonts.ps1

# 2) 合成三条音轨（numpy，无采样）
python engine/audio.py --track all
python engine/audio_qa.py

# 3) 渲一张关键帧看看
python engine/capture.py --html projects/knowledge/index.html `
  --out qa/stills/knowledge --width 1920 --height 1080 --duration 126 --still 17,60,90

# 4) 全片渲染（知识片约 2–3 分钟 @ 28fps）
python engine/capture.py --html projects/knowledge/index.html `
  --out out/knowledge/frames --width 1920 --height 1080 --duration 126 --fps 30

# 4b) 配音版：TTS → 104BPM 编曲 → 渲染 → 编码
python engine/tts.py
python engine/yuanfen_audio.py
python engine/capture.py --html projects/yuanfen/index.html `
  --out out/yuanfen/frames --width 1920 --height 1080 --duration 73.84 --fps 30
python engine/encode.py --frames out/yuanfen/frames `
  --audio projects/yuanfen/mix.wav --out out/yuanfen.mp4 --lufs -14

# 5) 编码 + 质检
python engine/encode.py --frames out/knowledge/frames `
  --audio projects/knowledge/audio.wav --out out/knowledge.mp4 --lufs -14
python engine/video_qa.py --file out/knowledge.mp4 --out qa/final/knowledge
```

或直接：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/render_all.ps1
```

## 四条片子的设计

### 01 知识大赏 ·《快，是被设计出来的》

六段叙事弧：钩子 → 时间轴 → 索引 → 向量 → 生成 → 上下文内存 → 判断 → 落点 → 引用。
- 1920×1080，30fps，126 秒，无旁白，双语字幕（中文 46px / 英文斜体 24px）。
- 深蓝黑底 `#05050E` + 金色 `#C9A96A`，五区布局：水印 / 章节标签 / 中央动画 / 注释带 / 字幕带。
- 真实数据：Cursor 2026-01-27 公开的 Merkle 树索引数据（中位首次可查 7.87s → 0.525s；P99 4.03h → 21s）。
- 结尾标注：界面为示意、数据截至 2026-10-20、风格参考 Vibe 知识大赏。

### 02 卡点 · VIBE CODING 128 BPM

- 1080×1920，24 秒，128 BPM，每 2 拍（0.9375s）一刀，共 12 个镜头。
- 镜头：0/1 倒计时 → VIBE CODING → 输入需求 → 生成 12 文件 → 写代码 → 改 diff → 12/12 测试 → 构建 1.2s → push → DEPLOYED → SHIP IT。
- 每拍做一次 1% 镜头 punch + 底部 64 段频谱脉冲；卡点与音频共用同一张 128 BPM 网格。

### 03 AI 音乐 · 由代码合成

- 1080×1920，30 秒，96 BPM，C# 小调；supersaw pad + sidechain + sub bass + pluck arp + lead。
- 画面是真实的 64 段频谱（`projects/music/spectrum.js`，由音频 FFT 预计算），不是随机波形。
- 15 秒 drop 与音频、画面、文字同时对齐；结尾明确写「由代码合成 · 无采样 · 无版权曲库」。

### 04 未见面的缘分 · 配音情感短片

- 1920×1080，73.84 秒，104 BPM，D 小调；金色衬线片名 + 中文配音 + 英文斜体字幕。
- **配音**：Edge TTS `zh-CN-XiaoxiaoNeural`（Warm），语速 +8%、音高 +2Hz；20 句独立生成，句级时间轴写入 `timing.js`。
- **鼓点重编**：太鼓落在 0 / 1.5 / 2 / 3.25 拍；light 段四踩进入；sync/line 段加 ghost kick 与 16 分踩镲；两次 16 分军鼓滚奏推进 drop。
- **混音**：人声出现时音乐 duck 38%；段落 RMS 从 −16.8 dB 推到 −13.8 dB，再回落到 −16.3 dB。
- **画面**：两枚光点 → 地点问号 → 穿过屏幕的光 → 双脑同频 → 悬崖之间点亮的线 → 致意卡。

## 技能检索（GitHub 优先）

`scripts/skill_radar.py` 从 5 组关键词检索 GitHub，去重 37 个候选，按 stars / 新鲜度 / 关键词 / Skill 属性评分，结果在：

- `skills/manifest.json`
- `skills/ACQUISITION.md`

实际采用的四条方法论：

| 来源 | 采用内容 |
|---|---|
| [vibe-knowledge-video](https://github.com/xiazhuo123456789/vibe-knowledge-video) | 五区布局、双语字幕、无旁白、77BPM 合成 BGM、结尾引用纪律 |
| [hbg-douyin-code-explainer-video](https://github.com/Mr-funny/hbg-douyin-code-explainer-video) | 「最终编码 MP4 才是交付对象」、BGM 稳定混音、抽帧质检 |
| [music-video-director-skill](https://github.com/guigulaoshi/music-video-director-skill) | 每 2 拍一刀、能量曲线、EDL 可复现 |
| [kinetic-typography-skills](https://github.com/iart-ai/kinetic-typography-skills) | 逐字/逐块入场、节拍脉冲 |

## 技能与部署

- 技能说明：`SKILL.md`（Agent 可直接读）
- 本地安装：`scripts/install.ps1` → `~/.agents/skills/douyin-coding-video`
  - **已执行**：本会话技能目录已出现 `douyin-coding-video`，可直接调用。
- GitHub 部署：`scripts/deploy_github.ps1`（需要 `gh auth login` 与 Git）
- 当前状态：**本机 gh 未登录、git 未安装，未执行推送**。脚本已做前置检查（无 Git 时退出码 2），登录后一条命令即可创建并推送。

详细步骤见 `docs/github-deploy.md`。

## 验证结果

| 片子 | 时长 | 大小 | 编码 | 综合响度 | True Peak | 静态比* | 黑帧/静音 |
|---|---:|---:|---|---:|---:|---:|---|
| 01 知识大赏 | 126.0s | 19.1 MB | H.264 High / yuv420p / 30fps | −14.0 LUFS | −2.3 dBTP | 0.785 | 0 / 0 |
| 02 卡点 | 24.0s | 6.9 MB | H.264 High / yuv420p / 30fps | −14.5 LUFS | −1.4 dBTP | 0.191 | 0 / 0 |
| 03 AI 音乐 | 30.0s | 13.8 MB | H.264 High / yuv420p / 30fps | −14.6 LUFS | −1.6 dBTP | 0.000 | 0 / 0 |
| 04 未见面的缘分 | 73.8s | 15.9 MB | H.264 High / yuv420p / 30fps | −14.0 LUFS | −2.9 dBTP | 0.673 | 0 / 0 |

\* 静态比 = 2fps 采样、480×270 缩略图相邻帧平均亮度差 < 1.0 的比例。知识片与缘分片是深色稀疏构图，指标偏高；实际 30fps 有颗粒、尘埃、扫描光带与场景动画，未用该指标冒充“画面密度达标”。

原始证据：

- `qa/final/knowledge/qa.json`、`qa/final/beat/qa.json`、`qa/final/music/qa.json`、`qa/final/yuanfen/qa.json`
- `qa/final/*/contact.png`（最终 MP4 抽帧联系表）
- `qa/audio/audio-qa.json`、`qa/audio/yuanfen-qa.json` + `qa/audio/*.png`
- `out/*.encode.json`（编码增益与响度）

音频身份：四条曲子均由代码合成，`projects/*/audio.json` 记录 BPM、调性、段落、SHA-256；`projects/yuanfen/timing.json` 另存 20 句配音的逐句起止。不是外部曲库，也没有采样。配音为 Edge TTS 合成，已在片尾标注。


## 版权与边界

- 所有画面由 Canvas/HTML 代码生成，无实拍、无第三方视频素材。
- 所有音乐由 `engine/audio.py` / `engine/yuanfen_audio.py` 逐样本合成，无采样、无版权曲库；`audio.json` 记录 BPM、调性、段落与 SHA-256。
- 配音由 Edge TTS 合成（`zh-CN-XiaoxiaoNeural`），不是真人；片尾与 README 均已标注。
- 风格参考抖音「Vibe 知识大赏」系列（@Iwanau / @Juno / 叁号暗房），只借鉴版式与方法，不复制原片。
- 产品名与数据来自公开文档，界面为示意；发布前请自行复核引用与平台条款。
