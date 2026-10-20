# 事实来源

数据与功能描述截至 2026-10-20，以官方文档为准。

1. Cursor, “Securely indexing large codebases”, 2026-01-27.
   https://cursor.com/blog/secure-codebase-indexing
   - Merkle tree、语法分块、embedding 缓存、simhash 复用。
   - 中位仓库 time-to-first-query 7.87s → 0.525s；P99 4.03h → 21s；同团队代码库平均 92% 相似。

2. TRAE, “SOLO is All You Need”, 2025-07-17.
   https://www.trae.ai/blog/product_solo
   - SOLO 端到端接管需求 → 代码 → 部署；Context Engineering。

3. Anthropic, “How the agent loop works”, Claude Code Docs.
   https://code.claude.com/docs/en/agent-sdk/agent-loop
   - 上下文接近上限时自动 compact，把较早历史压缩成摘要；子代理独立上下文。

4. 风格参考：抖音「Vibe 知识大赏」系列（@Iwanau / @Juno / 叁号暗房）。
   https://github.com/xiazhuo123456789/vibe-knowledge-video
   - 五区布局、双语字幕、无旁白、77BPM、逐帧运动密度。

5. 质检方法：hbg-douyin-code-explainer-video。
   https://github.com/Mr-funny/hbg-douyin-code-explainer-video
   - 最终 MP4 抽帧、BGM 稳定混音、H.264/yuv420p/48kHz 检查。

> 视频中的产品界面均为代码绘制的示意图，不是任何产品的实际截图。
