<p align="center">
  <img src="docs/readme/cover.png" alt="Music Video Director pipeline: song, footage and a director's note go in; the mvd CLI downloads and analyzes them; the AI agent reads the keyframes and writes the edit plan; you approve it; mvd validates and renders the finished music video" width="100%">
</p>

# Music Video Director (MV大导演)

**An AI agent skill that turns music + raw footage into an edited music video — with beat sync, lyric imagery matching, shot grammar, and emotional arc planning.**
**一个让 AI 帮你剪音乐视频的 skill：一首歌 + 一堆素材 + 一句导演意图，剪出卡点成片。**

Works with any AI agent that can run shell commands and (optionally) read images.

[How to use](#how-to-use--怎么用) · [How it works](#how-it-works) · [The `mvd` CLI](#the-mvd-cli) · [EDL format](#edl-format) · [License](#license)

## 简介

这是一个让 AI 帮你剪音乐视频的 skill。给它一首歌 + 一堆素材（B站/YouTube 链接或本地文件）+ 一句导演意图（比如"高燃混剪"或"伤感抒情"），它会自动：分析歌曲节奏与歌词、识别素材里的镜头、按音乐结构和歌词意象编排剪辑表（EDL）、最后渲染出成片。

适用于任何能跑 shell 命令的 AI agent。

---

## How to use · 怎么用

**1. Install the skill · 装上技能** (Claude Code — other agents: see [Installation](#installation))

```bash
curl -fsSL https://raw.githubusercontent.com/guigulaoshi/music-video-director-skill/main/skill.md \
  -o ~/.claude/commands/mv-director.md
```

**2. Make sure ffmpeg is installed · 装好 ffmpeg** — `brew install ffmpeg` on macOS. Everything else installs itself on first run. 其余依赖第一次运行时自动安装。

**3. Run it and answer three questions · 运行，回答三个问题**

```
/mv-director
```

| The agent asks for · 它会问你要 | Example · 例子 |
|---|---|
| **Song** · 歌 | a YouTube / Bilibili link or a local audio file · 链接或本地文件（只取音频） |
| **Footage** · 素材 | one or more video links or files · 一个或多个视频链接或文件 |
| **Direction** · 导演意图 | *"High-energy performance edit — cut on every beat in the chorus, breathing room in the verses."* · "高燃混剪，副歌每拍一切" |

**4. Approve the plan, then it renders · 看剪辑方案，点头就出片** — before rendering, the agent shows the emotional arc, cuts per section and the cut list with lyric context. Say *render*, or ask for changes (*"make the chorus faster"*, *"use more of clip 2"*). The finished `.mp4` lands in the project folder, next to `edit_plan.json`, which you can edit and re-render without re-analyzing anything.
渲染前会先给你看情绪走向、每段几刀、带歌词的剪辑表；说"渲染"就出片，也可以让它改节奏、换素材。

<table>
  <tr>
    <td width="50%"><img src="docs/readme/cli-help.png" alt="Output of mvd --help listing the six commands: analyze-audio, detect-scenes, download, install, render, validate"></td>
    <td width="50%"><img src="docs/readme/cli-validate.png" alt="Output of mvd validate on a three-cut edit plan: two checks fail because cut 1 and cut 3 reuse overlapping footage from the same clip"></td>
  </tr>
  <tr>
    <td align="center"><sub>The <code>mvd</code> CLI the agent drives · 智能体调用的命令行工具</sub></td>
    <td align="center"><sub><code>mvd validate</code> catching reused footage before a slow render · 渲染前先查出重复用的镜头</sub></td>
  </tr>
</table>

---

## How it works

1. You provide: a music audio URL/file, video clip URLs/files, and a director's instruction.
2. The agent downloads everything, analyzes the audio (beats, structure, lyrics) and clips (scene detection, keyframe extraction) using the `mvd` CLI.
3. The agent examines the keyframe images — using image analysis if available, or scene metadata otherwise — and describes each scene.
4. The agent generates a shot-by-shot Edit Decision List (EDL) applying professional editorial rules: beat-sync timing, lyric imagery matching, shot grammar, energy-arc matching, color coherence.
5. The agent presents the edit plan for your review and approval.
6. On approval, the agent validates the EDL and renders the final `.mp4`.

**Division of labor**: The `mvd` Python CLI handles technical work (downloading, beat detection, scene detection, ffmpeg rendering). The AI agent handles all creative work (scene description, edit planning, editorial judgment). No AI API calls from the CLI — the agent is the AI.

---

## Installation

### One step

Drop `skill.md` wherever your agent looks for skills. Everything else installs itself on first run.

**Claude Code:**
```bash
curl -fsSL https://raw.githubusercontent.com/guigulaoshi/music-video-director-skill/main/skill.md \
  -o ~/.claude/commands/mv-director.md
```
Then invoke with `/mv-director`. The skill will auto-install the `mvd` Python toolkit on first use.

**Other agents:** paste the contents of `skill.md` into the agent's system prompt, or reference it as a task file per that agent's convention. The skill handles its own dependency installation at runtime.

### The only true prerequisite: ffmpeg

ffmpeg is a system binary that pip cannot install. If the auto-installer reports it missing:

```bash
# macOS
brew install ffmpeg

# Linux
sudo apt-get install -y ffmpeg

# Windows
winget install ffmpeg
```

Everything else (`yt-dlp`, `librosa`, `whisper`, `scenedetect`, …) is installed automatically by the skill on first run.

---

## Usage

Invoke the skill (or paste its contents to your agent) and follow the prompts. The agent will ask for:

- **Audio source**: YouTube/Bilibili URL or local file — audio is extracted, video from this source is discarded
- **Video clips**: One or more URLs or local file paths for footage
- **Director's instruction**: The creative direction — mood, story, approach

Example director's instructions:
- *"Melancholic urban isolation that builds toward cathartic release. Tight beat-sync on the chorus."*
- *"High-energy performance edit — cut on every beat in the chorus, breathing room in the verses."*
- *"Abstract and dreamy. Imagery should be metaphorical, not literal. Use cool tones throughout."*
- *"Tell the story of someone falling in love — intimate close-ups in the verse, wide open spaces in the chorus."*

---

## The `mvd` CLI

The skill uses these commands internally. You can also run them directly:

```bash
# Check / install dependencies
mvd install -y

# Download from URL or copy local file
mvd download "https://www.youtube.com/watch?v=..." --output-dir ./project --name "clip1"
mvd download "https://www.youtube.com/watch?v=..." --output-dir ./project --audio-only --name "audio"

# Analyze audio (beats, structure, lyrics)
mvd analyze-audio ./project/audio.mp3 --output ./project/audio_analysis.json

# Detect scenes and extract keyframes
mvd detect-scenes ./project/clip1.mp4 --output ./project/clip1_scenes.json

# Check an EDL for overlapping / out-of-order / repeated cuts (exit 1 on errors)
mvd validate ./project/edit_plan.json

# Render from an EDL
mvd render ./project/edit_plan.json --output ./project/output.mp4
```

See `mvd --help` or `mvd <command> --help` for full options.

---

## Output Files

All outputs land in a project directory (default: `/tmp/mvd_YYYYMMDD_HHMMSS/`):

```
project/
├── sources/
│   ├── audio.mp3          # Extracted music audio
│   ├── clip1.mp4          # Downloaded / copied clips
│   └── clip2.mp4
├── audio_analysis.json    # Beats, sections, energy curve, lyrics
├── clip1_scenes.json      # Scene boundaries + keyframe paths
├── clip2_scenes.json
├── keyframes/
│   ├── clip1/
│   │   ├── scene_0000.jpg # Keyframe images for agent visual analysis
│   │   └── ...
│   └── clip2/
├── edit_plan.json         # The EDL — re-renderable artifact
└── output.mp4             # Final rendered music video
```

The `edit_plan.json` is the key artifact: edit it manually and re-run `mvd render` to produce a new cut without re-analyzing anything.

---

## EDL Format

The edit plan JSON the agent generates:

```json
{
  "metadata": {
    "song_title": "...",
    "bpm": 128.5,
    "total_duration": 213.45,
    "total_cuts": 47,
    "avg_shot_length": 4.5,
    "emotional_arc": "Opens with isolation, builds toward cathartic release, resolves with quiet peace."
  },
  "audio_file": "/absolute/path/to/audio.mp3",
  "output_file": "/tmp/mvd_xxx/output.mp4",
  "cuts": [
    {
      "n": 1,
      "timeline_start": 0.000,
      "timeline_end": 7.917,
      "source_file": "/absolute/path/to/clip1.mp4",
      "source_in": 0.300,
      "source_out": 8.217,
      "section": "intro",
      "lyric": null,
      "description": "Wide exterior, empty city street at dusk",
      "rationale": "Establishes the lonely urban world before vocals enter"
    }
  ]
}
```

---

## Editorial Philosophy (what the skill encodes)

The skill embeds professional music video editorial knowledge:

- **Beat sync**: 1-frame-early rule (cuts land 2 frames before the beat for perceived tightness)
- **Musical structure**: Different visual treatment for intro / verse / pre-chorus / chorus / bridge / outro
- **Energy matching**: ASL (average shot length) tracks the song's dynamic envelope
- **Shot grammar**: 30° rule, Kuleshov effect, match cuts, motion vector matching, shot scale progression
- **Lyric imagery**: Literal / conceptual / metaphorical / counterpoint approaches
- **Color coherence**: Consecutive shot palette compatibility; color as emotional signal
- **Repetition avoidance**: 30-second window; same scene twice = noticed
- **Emotional arc**: Visual story has a beginning, middle, peak, and resolution
- **Scene boundary respect**: Detected scene atoms are never split

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `yt-dlp` | Download from YouTube, Bilibili, and 1000+ sites |
| `librosa` | Beat tracking, energy analysis, structural segmentation |
| `openai-whisper` | Lyric transcription with timestamps |
| `scenedetect` | Scene boundary detection |
| `ffmpeg-python` | FFmpeg Python bindings |
| `ffmpeg` (system) | Video encoding, decoding, rendering |
| `numpy`, `scipy` | Signal processing |
| `Pillow` | Image handling |
| `click` | CLI framework |

---

## License

MIT

---

Made by **guigulaoshi** · [itch.io](https://guigulaoshi.itch.io) · [GitHub](https://github.com/guigulaoshi) · [YouTube](https://www.youtube.com/@guigulaoshi) · [X](https://x.com/guigulaoshi) · [TikTok](https://www.tiktok.com/@guigulaoshi) · [抖音](https://www.douyin.com/user/MS4wLjABAAAAmWbEAlX8SvUu3RUFu48ArUSOqK9-2cTOC78Byiqe0GY) · [哔哩哔哩](https://space.bilibili.com/3546730639395688) · [小红书](https://www.xiaohongshu.com/user/profile/6090be480000000001005d88)
