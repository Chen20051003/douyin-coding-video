# 剧本 ·《快，是被设计出来的》

> 1920×1080 / 30fps / 126s / 77BPM / 无旁白 / 双语字幕

| 时间 | 中文 | English |
|---|---|---|
| 0.0–3.6s | 同一句需求。 | Same prompt. |
| 3.6–7.2s | 为什么有人 3 秒出代码？ | Why does one ship in three seconds? |
| 7.2–10.8s | 有人却改到凌晨。 | Another debugs until dawn. |
| 10.8–14.0s | 差别不在模型大小。 | The difference is not model size. |
| 20.0–23.5s | 2021，先补全一行。 | 2021: it completes a line. |
| 23.5–27.0s | 2023，读懂整个文件。 | 2023: it reads the whole file. |
| 27.0–30.5s | 2025，接管终端与仓库。 | 2025: it takes the terminal. |
| 30.5–34.0s | 2026，开始管理上下文。 | 2026: it manages context. |
| 34.0–37.8s | 第一步，先给整座城市画地图。 | Step one: map the entire city. |
| 37.8–41.4s | Merkle 树记住每个文件的哈希。 | A Merkle tree hashes every file. |
| 41.4–45.0s | 只同步变动的街区。 | Only changed blocks get synced. |
| 45.0–48.8s | 中位仓库首次可查：7.87 秒 → 0.525 秒。 | Median first query: 7.87s to 0.525s. |
| 48.8–52.0s | 第 99 百分位：4.03 小时 → 21 秒。 | P99: 4.03 hours to 21 seconds. |
| 52.0–55.6s | 第二步，把代码切成语法块。 | Step two: chunk code by syntax. |
| 55.6–59.2s | 再压成向量，按距离检索。 | Embed each chunk. Search by distance. |
| 59.2–62.6s | 改一个函数，只重算一块。 | Edit one function, re-embed one chunk. |
| 62.6–66.0s | 第三步，先猜，再验。 | Step three: predict, then verify. |
| 66.0–69.5s | 只回写差异，不重写全文。 | Write back only the diff. |
| 69.5–73.0s | 于是它看起来像在思考。 | So it looks like it is thinking. |
| 73.0–76.6s | 但真正的内存，是上下文窗口。 | But the real RAM is the context window. |
| 76.6–80.0s | 装得下整个仓库吗？装不下。 | Can it hold the whole repo? No. |
| 80.0–83.6s | 于是它学会遗忘。 | So it learns to forget. |
| 83.6–87.0s | 旧对话被压缩成摘要。 | Old turns become a summary. |
| 87.0–90.6s | 子代理各拿一小块内存。 | Subagents each hold a slice. |
| 90.6–94.0s | 内存管理，才是隐形的战场。 | Memory management is the hidden war. |
| 94.0–97.6s | 可是，快不等于对。 | But fast is not correct. |
| 97.6–101.2s | 它可能自信地改错一行。 | It can confidently break a line. |
| 101.2–104.8s | 工具越快，判断越贵。 | The faster the tool, the more judgment costs. |
| 104.8–108.0s | 所以真正的用法是—— | So the real workflow is - |
| 108.0–111.6s | 把重复交给机器。 | Give repetition to the machine. |
| 111.6–115.0s | 把判断留给自己。 | Keep judgment for yourself. |
| 115.0–118.0s | 快，是被设计出来的。 | Speed is designed. |
| 118.0–121.5s | 而方向，是你给的。 | Direction is yours. |

## 引用

- Cursor, “Securely indexing large codebases”, 2026-01-27 — cursor.com/blog/secure-codebase-indexing
- TRAE, “SOLO is All You Need”, 2025-07-17 — trae.ai/blog/product_solo
- Anthropic, “How the agent loop works”, Claude Code Docs — code.claude.com/docs/en/agent-sdk/agent-loop

> 产品界面为代码绘制的示意，不是实际截图。数据截至 2026-10-20。
