# 剧本 / 分镜 · AI MUSIC（代码合成）

1080×1920 / 30fps / 30s / 96 BPM / C# 小调。

| 时间 | 段落 | 画面 | 文案 |
|---|---|---|---|
| 0–6s | intro | 深紫星空、粒子、环形刻度 | 如果代码会唱歌 |
| 6–11s | prompt | PROMPT.TXT 卡片逐字输入 | 写一首关于代码的歌 |
| 11–15s | code | 旋转环 + `CODE`，频谱开始生长 | 每一行，都是一个音色 |
| 15–24s | drop | 环爆发、粒子扩张、画面抖动；`SOUND` | 没有采样，只有数学 |
| 24–30s | outro | 环回落，`AI MUSIC` 标志 | 由代码合成 · 无采样 · 无版权曲库 |

音频：supersaw pad + sidechain + sub bass + pluck arp + lead motif；15.0s drop。
画面：64 段频谱来自真实音频 FFT（`spectrum.js`），不是随机数。
