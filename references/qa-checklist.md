# 最终质检清单

## 1. 音频（编码前）

```powershell
python engine/audio_qa.py
```

- [ ] 无削波（`clip_ratio = 0`）
- [ ] 无长静音（`silence_ratio < 0.01`）
- [ ] `audio.json` 的 BPM / 调性 / 时长与分镜一致
- [ ] 节拍核验：低频能量 lag 在 ±60ms 内；知识片 77BPM、卡点 128BPM、音乐 96BPM
- [ ] 看 `qa/audio/*.png`：有段落推进，不是一条直线

## 2. 源帧（编码前）

- [ ] 关键时间点抽帧：开场 / 标题 / 每个机制高潮 / 结尾
- [ ] 文字不重叠、不溢出、不糊
- [ ] 行号与代码分栏；右对齐后已重置 `textAlign`
- [ ] 竖屏内容在 56px 安全区内
- [ ] 长英文单词不超框（`DEPLOYED` 用 150px，不是 210px）

## 3. 最终 MP4（编码后，必做）

```powershell
python engine/video_qa.py --file out/knowledge.mp4 --out qa/final/knowledge
```

- [ ] H.264 High / yuv420p
- [ ] 分辨率、fps、时长正确
- [ ] AAC / 48kHz / 2ch
- [ ] `black_events` 为空（或仅结尾 <0.15s）
- [ ] `silence_events` 为空
- [ ] 综合响度：知识 −14 ±1 LUFS；卡点/音乐 −12 ±2 LUFS
- [ ] True Peak ≤ −1.0 dBFS
- [ ] `motion.static_ratio < 0.25`
- [ ] 看 `contact.png`：五帧都有内容、无黑屏/半张空页

## 4. 发布前

- [ ] 数据与引用标注日期
- [ ] 界面标「示意」
- [ ] 音乐来源写明「代码合成 · 无采样」
- [ ] 不伪造抖音热度、播放量、排名
- [ ] 平台条款 / 字体许可 / 引用准确性复核
