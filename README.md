# 🎬 IRAM Video: Universal Prompt-to-Video AI Engine

An autonomous, prompt-driven video generation engine that transforms **any natural language prompt or technical topic** into a broadcast-quality 1080p MP4 video, complete with a **high-CTR YouTube thumbnail** and **ready-to-paste metadata & chapters**.

---

## 🏛️ Architecture & Stack

```
User Prompt ──► Google Gemini 3.8 Flash (AI Creative Director)
                         │
        ┌────────────────┼────────────────┬────────────────┐
        ▼                ▼                ▼                ▼
   Screenplay JSON   Edge Neural TTS   Pillow 1080p     Numpy Mood Synth
   (Scenes, Layouts) (Aria / Chris)    (Smart-Wrap HUD) (Cyber, Lo-Fi)
        │                │                │                │
        └────────────────┴────────┬───────┴────────────────┘
                                  ▼
                         FFMPEG Master Engine
                       (Fade Transitions + Ducking)
                                  │
                                  ▼
                     🎬 Master 1080p MP4 Video
                     🖼️ High-CTR YouTube Thumbnail (.png)
                     📋 YouTube Chapters & Metadata (.txt)
```

---

## 🚀 Quick Usage

Generate a video from any topic directly in your terminal:

```bash
# 1. Basic usage:
iram-video "Explain how quantum computing works"

# 2. Specify output file and narrator voice:
iram-video "What is Rust memory safety and ownership model" -o rust_safety.mp4 --voice aria

# 3. Specify scene count, music mood, and style:
iram-video "Top 5 Linux tools every developer should know in 2026" --scenes 5 --music cyber --voice christopher
```

---

## 🎛️ CLI Options

| Argument | Description | Default |
| :--- | :--- | :--- |
| `prompt` | The topic, idea, or outline for the video *(Positional, Required)* | — |
| `-o, --output` | Target file path for the output `.mp4` video | `./<slug>.mp4` |
| `--voice` | Voice persona (`aria`, `jenny`, `emma`, `christopher`, `guy`, `brian`, `eric`) | `aria` (Female) |
| `--scenes` | Target number of scenes to generate | `auto` (Gemini decides) |
| `--music` | Mood of background soundtrack (`cyber`, `lofi`, `tech`, `ambient`, `none`) | `cyber` |
| `--style` | Visual/editorial style hint (e.g. `dark mode`, `minimal`, `fast-paced`) | `None` |
| `--no-thumbnail`| Skip generating the companion YouTube thumbnail `.png` | `False` |

---

## 🌟 Key Features

1. **Zero Text Overlap Guaranteed**: Every slide uses dynamic word wrapping and computed bounding-box collision detection. Text never bleeds out of boxes or off the canvas.
2. **Official Google GenAI Direction**: Powered by Google's official `gemini-3.8-flash` model via the `google-genai` SDK.
3. **High-CTR Thumbnail Included**: Automatically creates an eye-catching 1280x720 thumbnail ready for YouTube Studio.
4. **Ready-to-Paste Chapters & SEO**: Exports timed chapter markers, descriptions, and tags alongside the video.
5. **No Cloud GPU Bills**: Video compositing, slide rendering, music synthesis, and voice generation run locally on your system.
