---
name: douyin-coding-video
description: "抖音情绪/知识类短视频的纯代码生成流水线：知识大赏横屏、128BPM 卡点、96BPM AI 音乐可视化、104BPM 配音情感短片。当用户要「做一条抖音知识视频」「知识大赏风格」「卡点视频」「AI 音乐视频」「未见面的缘分/情感旁白视频」时使用。画面由 Canvas/HTML 代码生成，音乐由 numpy 逐样本合成，配音可用 Edge TTS。"
version: "1.0.0"
---

# 抖音编程短视频 · 代码生成流水线

> 三条可复用配方：**知识大赏（横屏）**、**128 BPM 卡点（竖屏）**、**96 BPM AI 音乐可视化（竖屏）**。
> 画面 100% 代码生成，无实拍、无版权素材；音乐 100% numpy 合成，可核对来源与节拍。

## 何时使用

- 「做一条抖音知识大赏风格的视频」「把 AI 编程软件讲成知识大片」
- 「做一条卡点视频」「编程/代码主题的节奏剪辑」
- 「做一条 AI 音乐视频」「代码生成音乐 + 可视化」
- 需要**成片 + 可复用源码 + 验证结果**，而不是只给方案

## 三条配方（先选一条）

| 配方 | 画幅 | 时长 | BPM | 关键约束 |
|---|---|---|---|---|
| 知识大赏 | 1920×1080 | 119–166s | 76–78 | 五区布局、双语字幕、无旁白、结尾引用 |
| 卡点 | 1080×1920 | 20–30s | 120–140 | 每 2 拍一刀、安全区、节拍脉冲 |
| AI 音乐 | 1080×1920 | 24–40s | 90–110 | 频谱驱动、drop 对齐、来源声明 |
| 情感短片（配音） | 1920×1080 | 60–90s | 100–110 | 中文配音、句级时间轴、音乐 ducking、鼓点重编 |

## 七步流水线

```
选题核实 → 剧本 → 分镜 → 关键静帧 → 逐帧渲染 → 音频合成/编码 → 最终 MP4 质检
```

### 1. 选题核实

- 所有年份、产品名、数字必须来自**公开文档**，写进 `references/sources.md` 并标日期。
- 没有把握的数字宁可不写；界面一律标「示意」。
- 不伪造抖音热度、播放量、排名。

### 2. 剧本（`script.md`）

- 知识大赏：每句 2.5–4 秒，中文主句 ≤20 字，**每句都有英文斜体对照**。
- 卡点：一句话 + 一个动作，按 2 拍（0.9375s @128BPM）切。
- AI 音乐：每 6 秒一个词/一句，drop 处只留关键词。

### 3. 分镜（`storyboard.md`）

每个镜头写：时间区间 / 构图 / 进场-主运动-出场 / 顶部标签 / 注释 / 双语字幕 / 转场。
转场从内容长出来（线变地平线、卡片飞散），不要默认黑场淡入。

### 4. 关键静帧

先渲 3–5 张关键帧目检：开场钩子、机制高潮、结尾卡。
**必须**检查：文字不重叠、行号不压字、长英文不超框、竖屏不越安全区。

### 5. 逐帧渲染

```powershell
python engine/capture.py --html projects/knowledge/index.html `
  --out out/knowledge/frames --width 1920 --height 1080 --duration 126 --fps 30
```

页面契约：

```js
function render(t) { /* 只依赖 t，不读 Date/Math.random */ }
window.render = render;
window.__ready = true;
```

- 字体用本地 `@font-face`，`document.fonts.ready` 之后再截图。
- 截图用 JPEG q94，1080p 约 28 fps 渲染速度。
- 断点续渲：`--resume`。

### 6. 音频与编码

```powershell
python engine/audio.py --track all
python engine/audio_qa.py
python engine/encode.py --frames out/knowledge/frames `
  --audio projects/knowledge/audio.wav --out out/knowledge.mp4 --lufs -14
```

- 知识大赏：77 BPM，A 小调，pad + 钢琴 + 低音提琴 + 轻打击。
- 卡点：128 BPM，F 小调，四踩 + 军鼓 + 8 分音符贝斯 + 琶音。
- AI 音乐：96 BPM，C# 小调，supersaw + sidechain + drop。
- 情感短片：104 BPM，D 小调，太鼓 0/1.5/2/3.25 拍 + 四踩 + 弦乐固定音型；人声出现时 duck 38%。
- 响度：知识 −14 LUFS，卡点/音乐/情感 −12～−14 LUFS，True Peak ≤ −1.2 dBFS。

### 配音版（`projects/yuanfen` 为范本）

```powershell
# 1) 逐句 TTS + 句级时间轴（Edge TTS）
python engine/tts.py
# 2) 104BPM 编曲 + 人声 ducking 混音
python engine/yuanfen_audio.py
# 3) 画面读 timing.js，按句切场景
python engine/capture.py --html projects/yuanfen/index.html `
  --out out/yuanfen/frames --width 1920 --height 1080 --duration 73.84 --fps 30
# 4) 编码 + 质检
python engine/encode.py --frames out/yuanfen/frames `
  --audio projects/yuanfen/mix.wav --out out/yuanfen.mp4 --lufs -14
python engine/video_qa.py --file out/yuanfen.mp4 --out qa/final/yuanfen
```

- 配音默认 `zh-CN-XiaoxiaoNeural`，`rate=+8%`、`pitch=+2Hz`；需要更活泼可换 `XiaoyiNeural`，更沉稳可换 `YunjianNeural`。
- 生成后必须核对每句时长与字幕时间；句间留 0.45s，重点句 0.7–0.8s。
- 不要让配音和字幕各写一套文案；`script.json` 是唯一来源。

### 7. 最终 MP4 质检

```powershell
python engine/video_qa.py --file out/knowledge.mp4 --out qa/final/knowledge
```

`qa.json` 必看：分辨率 / fps / 编码 / 时长 / 黑帧 / 静音 / 响度 / 运动密度 / 抽帧联系表。
**浏览器静帧不能替代最终 MP4 抽帧。**

## 硬规则（踩过的坑）

1. **行号与代码分栏**：`ctx.textAlign` 会残留。画完右对齐行号必须重置 `textAlign="left"`，代码起始 x 要大于行号右边界。
2. **双层 alpha**：`HF.text` 的 `alpha` 是覆盖值；外层已有 `globalAlpha` 时不要重复相乘。
3. **浮动误差**：`(u-10.4)/1.6` 在 `u=12` 可能得到 `0.9999999999999998`，判断完成要用 `u >= 12` 而不是 `>=1`。
4. **长英文超框**：`DEPLOYED` 在 1080 宽、210px 时会被裁切；先 `measureText` 或降到 150px。
5. **扫光别画成色块**：用 2px 竖线 + 径向光晕，不要用 80px 宽的线性渐变矩形。
6. **卡拉 OK 式字幕**：知识大赏每句中文下必须有英文斜体；字号 46/24，y≈930/974。
7. **节拍核验**：低频能量峰值会比 kick 触发点晚 20–40ms（pitch sweep 造成），不要据此改时间轴；以合成代码的 `place()` 时间为准。
8. **音乐身份**：`audio.json` 记录 BPM/调性/段落/`sha256`/生成器；仅凭波形或时长不能证明曲目身份。
9. **字体**：仓库不提交 40MB 字体；运行 `scripts/fetch_fonts.ps1` 从系统复制 Noto Sans/Serif SC，或自行安装。
10. **不要伪造数据**：引用公开文档并标日期；产品界面标「示意」。

## 目录

```
engine/            capture / audio / encode / video_qa / hf.js
projects/          三条片子的 index.html + 剧本 + 分镜
skills/            GitHub 技能雷达结果（manifest.json / ACQUISITION.md）
scripts/           skill_radar / install / deploy_github / render_all
qa/                音频频谱、静帧、最终 MP4 抽帧与 qa.json
```

## 发布文案模板

```
# 知识大赏
CODE 知识大赏 | 《快，是被设计出来的》
AI 编程软件为什么快？拆开三层：索引、生成、上下文内存。
#知识大赏 #AI编程 #Cursor #TRAE #ClaudeCode

# 卡点
VIBE CODING · 128BPM
一句话 → 一个能打开的链接。8 个八拍，卡点看完。
#卡点视频 #vibecoding #编程 #AI

# AI 音乐
如果代码会唱歌 · 96BPM
没有采样，只有数学。PROMPT → CODE → SOUND。
#AI音乐 #代码音乐 #可视化
```

## 边界

- 本技能不下载、不复用任何第三方视频/音乐素材。
- 风格参考抖音「Vibe 知识大赏」，仅借鉴版式与方法，不复制原片。
- 发布前自行确认平台条款、字体许可与引用准确性。
