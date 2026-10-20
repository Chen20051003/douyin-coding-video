"""Skill radar: search GitHub, score candidate video skills, write a manifest.

Usage:
  python scripts/skill_radar.py --cache research/github-search-raw.json
  python scripts/skill_radar.py --live            # needs GitHub API access
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "skills"
CACHE = ROOT / "research" / "github-search-raw.json"

QUERIES = [
    "douyin video skill",
    "short-video agent skill",
    "knowledge video skill",
    "beat sync video skill",
    "ai music generation skill",
]

KEYWORDS = ["douyin", "抖音", "short-video", "短视频", "knowledge", "知识", "beat", "卡点", "music", "音乐", "skill", "agent"]


def search_live() -> list[dict]:
    rows = []
    for q in QUERIES:
        url = (
            "https://api.github.com/search/repositories?q="
            + urllib.parse.quote(q)
            + "&sort=stars&order=desc&per_page=8"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "dsh-skill-radar", "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8"))
        for it in data.get("items", []):
            rows.append(
                {
                    "query": q,
                    "full_name": it["full_name"],
                    "stars": it["stargazers_count"],
                    "updated": it["updated_at"],
                    "desc": it.get("description") or "",
                    "url": it["html_url"],
                }
            )
    return rows


def load_cache() -> list[dict]:
    raw = json.loads(CACHE.read_text(encoding="utf-8-sig"))
    return raw if isinstance(raw, list) else []


def score(row: dict, today: dt.date) -> float:
    s = math.log10(max(row["stars"], 1) + 1) * 2.2
    try:
        updated = dt.date.fromisoformat(row["updated"][:10])
        days = (today - updated).days
        s += 2.2 if days <= 30 else 1.2 if days <= 90 else 0.0
    except ValueError:
        pass
    text = (row["full_name"] + " " + row["desc"]).lower()
    s += sum(0.8 for k in KEYWORDS if k in text)
    if re.search(r"skill|agent", text):
        s += 1.2
    if "douyin" in text or "抖音" in text:
        s += 1.0
    return round(s, 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=str(CACHE))
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--top", type=int, default=12)
    args = ap.parse_args()

    rows = search_live() if args.live else load_cache()
    if not rows:
        raise SystemExit("no rows: run --live or provide a cache")
    seen = {}
    for r in rows:
        seen.setdefault(r["full_name"], r)
    today = dt.date.today()
    ranked = sorted(seen.values(), key=lambda r: score(r, today), reverse=True)
    for r in ranked:
        r["score"] = score(r, today)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "manifest.json").write_text(json.dumps(ranked[: args.top], ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# GitHub 技能雷达 · 检索记录",
        "",
        f"- 生成时间：{dt.datetime.now().isoformat(timespec='seconds')}",
        f"- 数据源：{'GitHub Search API（实时）' if args.live else 'research/github-search-raw.json（本次检索原始结果）'}",
        f"- 去重候选：{len(seen)} 个",
        "",
        "| 排名 | 仓库 | Stars | 评分 | 与本项目的关系 |",
        "|---:|---|---:|---:|---|",
    ]
    relation = {
        "xiazhuo123456789/vibe-knowledge-video": "知识大赏风格逆向；五区布局、双语字幕、77BPM 合成 BGM",
        "Mr-funny/hbg-douyin-code-explainer-video": "中文代码讲解视频；最终 MP4 质检与 BGM 稳定混音清单",
        "guigulaoshi/music-video-director-skill": "卡点剪辑语法；1 帧提前、能量曲线、EDL 可复现",
        "iart-ai/kinetic-typography-skills": "动态字体；逐字/逐词入场与节拍对齐",
        "calesthio/OpenMontage": "大型代码化剪辑工程；仅借鉴分层结构",
    }
    for i, r in enumerate(ranked[: args.top], 1):
        lines.append(f"| {i} | [{r['full_name']}]({r['url']}) | {r['stars']} | {r['score']} | {relation.get(r['full_name'], '候选池')} |")
    lines += [
        "",
        "## 采用结论",
        "",
        "1. **知识大赏**：采用「Vibe 知识大赏」的五区布局、双语字幕、无旁白、77BPM 合成配乐；不复制原片素材。",
        "2. **代码讲解**：采用「先连续、再拆视觉」「最终编码 MP4 才是交付对象」的质检纪律。",
        "3. **卡点**：采用每 2 拍一刀、1 帧提前的剪辑语法；本项目用 128BPM、0.9375s/刀。",
        "4. **动态字体**：采用逐字/逐块入场与节拍脉冲；所有动画由 render(t) 纯时间函数驱动。",
        "5. **未采用**：需要下载第三方视频素材或版权曲库的方案，避免素材与授权风险。",
        "",
        "> 说明：以上为检索与取舍记录，不代表已安装或复制这些仓库的全部代码。",
    ]
    (OUT / "ACQUISITION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"ranked {len(ranked)} repos -> {OUT / 'manifest.json'}")
    for r in ranked[:5]:
        print(f"  {r['score']:5.2f}  {r['full_name']}  ({r['stars']} stars)")


if __name__ == "__main__":
    main()
