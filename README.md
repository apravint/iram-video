# 🎬 IRAM Video: Universal Bilingual Prompt-to-Video AI Engine (English & தமிழ்)

An autonomous, prompt-driven video generation engine that transforms **any natural language prompt or technical topic in English or Tamil (தமிழ்)** into a broadcast-quality 1080p MP4 video, complete with a **high-CTR YouTube thumbnail** and **ready-to-paste metadata & chapters**.

---

## 🏛️ Architecture & Stack

```
User Prompt (EN / தமிழ்) ──► Google Gemini 3.8 Flash (AI Creative Director)
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        ▼                             ▼                             ▼
   Screenplay JSON             Edge Neural TTS               Pillow 1080p
   (Scenes, Layouts)     (Aria / Pallavi / Valluvar)       (Noto Tamil / JetBrains)
        │                             │                             │
        └─────────────────────────────┼─────────────────────────────┘
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

### 1. English Video Generation
```bash
# English video with default female voice (Aria):
iram-video "Explain how quantum computing works"

# English video with male tech narrator (Christopher) and Lo-Fi soundtrack:
iram-video "What is Rust memory safety and ownership model" --voice christopher --music lofi
```

### 2. Tamil Video Generation (தமிழ்)
```bash
# Automatically detects Tamil script from the prompt:
iram-video "செயற்கை நுண்ணறிவு என்றால் என்ன?"

# Or specify Tamil language explicitly:
iram-video "Linux operating system basics" --lang ta --voice pallavi

# Tamil video with male voice (Valluvar):
iram-video "Python நிரலாக்க மொழி அறிமுகம்" --voice valluvar --music cyber
```

---

## 🎛️ CLI Options

| Argument | Description | Default |
| :--- | :--- | :--- |
| `prompt` | Topic, brief, or script in English or Tamil *(Positional, Required)* | — |
| `-o, --output` | Target file path for the output `.mp4` video | `./<slug>.mp4` |
| `--lang` | Language: `en` (English), `ta` (Tamil), or `auto` (auto-detect) | `auto` |
| `--voice` | Voice persona (`aria`, `christopher`, `jenny`, `pallavi` [Tamil female], `valluvar` [Tamil male]) | `auto` |
| `--scenes` | Target number of scenes to generate | `auto` |
| `--music` | Mood of background soundtrack (`cyber`, `lofi`, `tech`, `ambient`, `none`) | `cyber` |
| `--style` | Visual/editorial style hint (e.g. `dark mode`, `educational`, `minimal`) | `None` |
| `--no-thumbnail`| Skip generating the companion YouTube thumbnail `.png` | `False` |

---

## 🌟 Key Features

1. **Native Bilingual Support (English & தமிழ்)**: Full support for both English and Tamil typography, voice synthesis, and screenplay generation.
2. **Zero Text Overlap Guaranteed**: Every slide uses dynamic word wrapping and computed bounding-box collision detection. Text never bleeds out of boxes or off the canvas.
3. **Official Google GenAI Direction**: Powered by Google's official `gemini-3.8-flash` model via the `google-genai` SDK.
4. **Studio Neural Voices**: High-clarity voices across languages (English `Aria`, `Christopher`; Tamil `Pallavi`, `Valluvar`).
5. **High-CTR Thumbnail Included**: Automatically creates an eye-catching 1280x720 thumbnail with Tamil or English typography.
6. **Ready-to-Paste Chapters & SEO**: Exports timed chapter markers, descriptions, and tags alongside the video.
