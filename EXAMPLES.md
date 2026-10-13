# IRAM VIDEO ENGINE — MASTER EXAMPLES & PLAYBOOK

A complete, battle-tested reference guide containing every type of video you can generate with `iram-video`. 

All examples include exact command-line syntax, production flags, and expected outputs.

---

## 📑 Table of Contents
1. [Core Production Rules & Quality Standards](#1-core-production-rules--quality-standards)
2. [Vertical YouTube Shorts / Instagram Reels / TikTok (9:16)](#2-vertical-youtube-shorts--instagram-reels--tiktok-916)
3. [Tamil Videos & Music Clips (தமிழ் ஆவணப்படம் மற்றும் பாடல்கள்)](#3-tamil-videos--music-clips-தமிழ்-ஆவணப்படம்-மற்றும்-பாடல்கள்)
4. [Real YouTube Documentary Films (16:9 & 4K)](#4-real-youtube-documentary-films-169--4k)
5. [Custom Audio / Song Music Videos (`--bg-music`)](#5-custom-audio--song-music-videos---bg-music)
6. [Hollywood Cinema Trailers (`--cinema`)](#6-hollywood-cinema-trailers---cinema)
7. [Multi-Character Animated Feature Films (`--film`)](#7-multi-character-animated-feature-films---film)
8. [Specialized Directorial Templates (`--template`)](#8-specialized-directorial-templates---template)
9. [Developer Repository Showcases (`--brag`)](#9-developer-repository-showcases---brag)
10. [Web Studio, REST API & Autonomous Agents](#10-web-studio-rest-api--autonomous-agents)
11. [CLI Options & Argument Cheat Sheet](#11-cli-options--argument-cheat-sheet)

---

## 1. Core Production Rules & Quality Standards

When you run `iram-video`:
* **Zero Slide Cards in Shorts**: Under `--shorts` or `--real`, all programmatic cards and slide boxes are bypassed. Every single beat is rendered as authentic 1080p stock video clips (`.mp4` / `.webm`).
* **Original True Camera Colors**: The default color grade (`clean`, `documentary`, `none`) uses pure passthrough (`null`), preserving the 100% natural colors of source photos and videos without green/pink hue shifts.
* **Mastered Broadcast Audio**: Master audio is normalized to EBU R128 standard (**-14 LUFS**, True Peak -1.5 dB, 48kHz stereo) with automatic sidechain ducking under voiceovers.
* **Kinetic Hormozi Subtitles**: Centered, readable, auto-highlighting animated kinetic captions (yellow active keyword highlights).

---

## 2. Vertical YouTube Shorts / Instagram Reels / TikTok (9:16)

Shorts format enforces 1080x1920 (9:16 vertical), ultra-fast pacing (< 45s), high-retention narrative hooks, and centered subtitles.

### Example 2.1: High-Impact Motivation Short
```bash
python3 -m iram_video.cli "The Pain of Discipline or The Pain of Regret: Why Consistency Beats Talent" \
  --shorts \
  --real \
  --subtitles \
  --music energetic \
  -o ~/shorts_discipline.mp4
```

### Example 2.2: Focus & Dopamine Reset Short
```bash
python3 -m iram_video.cli "How 10 Minutes of Boredom Can Fix Your Broken Attention Span" \
  --shorts \
  --real \
  --subtitles \
  --music lofi \
  -o ~/shorts_dopamine.mp4
```

### Example 2.3: Quick Tech / Coding Insight Short
```bash
python3 -m iram_video.cli "Why Python 3.14 Free-Threaded GIL Changes Everything for Developers" \
  --shorts \
  --real \
  --subtitles \
  --music tech \
  -o ~/shorts_python_gil.mp4
```

### Example 2.4: Top-3 Countdown Listicle Short
```bash
python3 -m iram_video.cli "Top 3 Morning Habits of World-Class Performers" \
  --shorts \
  --listicle \
  --subtitles \
  --music energetic \
  -o ~/shorts_top3_habits.mp4
```

---

## 3. Tamil Videos & Music Clips (தமிழ் ஆவணப்படம் மற்றும் பாடல்கள்)

Full native Unicode Tamil support with neural voice personas:
* `--voice valluvar` — Authoritative, motivating male Tamil voice (`ta-IN-ValluvarNeural`).
* `--voice pallavi` — Warm, expressive female Tamil voice (`ta-IN-PallaviNeural`).

### Example 3.1: கம்பீரமான தமிழ் எழுச்சிப் பாடல் / Motivation Anthem (Shorts)
```bash
python3 -m iram_video.cli "உன் கனவை துரத்து: வீழ்ந்தாலும் எழுவோம், விடாமுயற்சியே வெற்றி தரும் ஒரு கம்பீரமான தமிழ் எழுச்சிப் பாடல்." \
  --lang ta \
  --voice valluvar \
  --music energetic \
  --real \
  --subtitles \
  --shorts \
  -o ~/tamil_motivation_anthem.mp4
```

### Example 3.2: மெல்லிய மெலடி மற்றும் இயற்கை கவிதை (Landscape 16:9)
```bash
python3 -m iram_video.cli "மழைக்கால மாலை பொழுதில் ஒரு மெல்லிய மெலடி பாடல் வரிகள். மேற்கு தொடர்ச்சி மலை, தூறல் மழை, பசுமையான தேயிலைத் தோட்டம் மற்றும் அமைதியான வாழ்க்கை பயணம்." \
  --lang ta \
  --voice pallavi \
  --music acoustic \
  --real \
  --subtitles \
  -o ~/tamil_rain_melody.mp4
```

### Example 3.3: சென்னை மெட்ரோ மற்றும் உள்கட்டமைப்பு ஆவணப்படம் (Full Documentary)
```bash
python3 -m iram_video.cli "சென்னை மெட்ரோ ரயில் கட்டம் 2: 116 கிலோமீட்டர் மெகா திட்டம் சென்னையின் போக்குவரத்தை எவ்வாறு புரட்டிப்போடும்?" \
  --lang ta \
  --voice valluvar \
  --real \
  --subtitles \
  --music documentary \
  -o ~/chennai_metro_doc.mp4
```

### Example 3.4: தமிழ் தொழில்நுட்ப விளக்கம் / Tech Explainer Short
```bash
python3 -m iram_video.cli "செயற்கை நுண்ணறிவு (AI) எவ்வாறு மனித சிந்தனையை மாற்றுகிறது? 3 முக்கிய உண்மைகள்." \
  --lang ta \
  --voice pallavi \
  --shorts \
  --real \
  --subtitles \
  --music tech \
  -o ~/tamil_ai_explained.mp4
```

---

## 4. Real YouTube Documentary Films (16:9 & 4K)

Documentary mode adopts Vox, Veritasium, and Johnny Harris pacing: conversational intelligence, physical cinematography, and structured narrative arcs.

### Example 4.1: High-Retention Science & Space Documentary
```bash
python3 -m iram_video.cli "The James Webb Space Telescope: Peering Into the Dawn of Cosmic Time" \
  --real \
  --subtitles \
  --music documentary \
  --transition fade \
  -o ~/james_webb_documentary.mp4
```

### Example 4.2: Macro Economics & Geopolitics
```bash
python3 -m iram_video.cli "The Silicon Chokepoint: How Extreme Ultraviolet Lithography Dictates Global Geopolitics" \
  --real \
  --subtitles \
  --music cinematic \
  -o ~/semiconductor_war.mp4
```

### Example 4.3: 4K UHD Master Production (`--4k`)
```bash
python3 -m iram_video.cli "Deep Sea Mysteries: The Alien Ecosystems of the Mariana Trench" \
  --real \
  --4k \
  --subtitles \
  --music ambient \
  -o ~/mariana_trench_4k.mp4
```

---

## 5. Custom Audio / Song Music Videos (`--bg-music`)

If you have an existing song or narration file (e.g. from Suno, Udio, a voice recording, or studio audio):

### Example 5.1: Synchronizing B-Roll to Your Own Song (.mp3/.wav)
```bash
python3 -m iram_video.cli "High-energy cinematic visuals matching an uplifting Tamil anthem." \
  --bg-music ~/Music/my_song.mp3 \
  --real \
  --shorts \
  --subtitles \
  -o ~/my_custom_music_video.mp4
```

### Example 5.2: Custom Voiceover / Podcast Audio with Real Footage
```bash
python3 -m iram_video.cli "Visual journey through mountain ridges, stormy seas, and night horizons." \
  --bg-music ~/Audio/podcast_snippet.wav \
  --real \
  -o ~/podcast_visualizer.mp4
```

---

## 6. Hollywood Cinema Trailers (`--cinema`)

Enforces 24 FPS cadence, 2.39:1 anamorphic widescreen letterbox, 35mm film grain, Inception-style low-frequency BRAAM soundscape effects, and a 3-act dramatic structure.

### Example 6.1: Epic Sci-Fi Movie Trailer
```bash
python3 -m iram_video.cli "THE EVENT HORIZON PROTOCOL: When mankind opened the doorway to the sixth dimension." \
  --cinema \
  --voice christopher \
  --subtitles \
  -o ~/event_horizon_trailer.mp4
```

### Example 6.2: Historical Warrior Epic (Tamil Cinema Trailer)
```bash
python3 -m iram_video.cli "சோழர் பேரரசின் கடல் ஆதிக்கம்: வங்காள விரிகுடாவை வென்ற மாவீரர்களின் கதை." \
  --cinema \
  --lang ta \
  --voice valluvar \
  --subtitles \
  -o ~/chola_dynasty_trailer.mp4
```

---

## 7. Multi-Character Animated Feature Films (`--film`)

Generates a procedural 2D animated film complete with character dialogue, expressive character mouth-flapping, procedural sets, score, and rolling Hollywood end credits.

### Example 7.1: Sci-Fi Space Odyssey (`nova,unit-7`)
```bash
python3 -m iram_video.cli "The Quantum Relic: An explorer and an eccentric android salvage an abandoned outpost." \
  --film \
  --cast nova,unit-7 \
  -o ~/quantum_relic_feature.mp4
```

### Example 7.2: Developer Comedy & Language War (`ferris,gopher`)
```bash
python3 -m iram_video.cli "The Great Refactor: Ferris the Rust Crab and the Go Gopher debate memory safety vs simplicity." \
  --film \
  --cast ferris,gopher \
  -o ~/rust_vs_go_comedy.mp4
```

---

## 8. Specialized Directorial Templates (`--template`)

### Example 8.1: Software Tutorial & Architecture (`--tutorial`)
Renders clean syntax-highlighted code windows, setup instructions, and architecture cards.
```bash
python3 -m iram_video.cli "How to Build High-Performance Microservices with Java 25 Virtual Threads" \
  --tutorial \
  --subtitles \
  -o ~/java_virtual_threads_tutorial.mp4
```

### Example 8.2: Head-to-Head Comparison (`--comparison`)
Renders split comparative cards with pros, cons, and performance stats.
```bash
python3 -m iram_video.cli "Linux vs Windows 11: Developer Workstation Deep Dive in 2026" \
  --comparison \
  --subtitles \
  -o ~/linux_vs_windows.mp4
```

### Example 8.3: Top-5 Ranked Listicle (`--listicle`)
Renders animated countdown badges (#5 through #1 WINNER).
```bash
python3 -m iram_video.cli "Top 5 Open Source AI Models That Run Locally on Linux" \
  --listicle \
  --subtitles \
  -o ~/top5_local_ai.mp4
```

### Example 8.4: Product Launch Promo (`--promo`)
Renders modern marketing cards with high-energy typography and metric badges.
```bash
python3 -m iram_video.cli "Introducing IRAM OS: The World's First Agentic Linux Distribution" \
  --promo \
  --subtitles \
  -o ~/iram_os_launch.mp4
```

### Example 8.5: Two-Host Conversational Podcast (`--podcast`)
Synthesizes a natural, back-and-forth dialogue between two distinct voices.
```bash
python3 -m iram_video.cli "Will Generative AI Replace Junior Developers or Turn Them Into Architects?" \
  --podcast \
  --subtitles \
  -o ~/ai_podcast_discussion.mp4
```

---

## 9. Developer Repository Showcases (`--brag`)

Auto-inspects any local Git repository or codebase, analyzes the stack, directory tree, and README, and turns it into a high-production developer showcase video:

```bash
python3 -m iram_video.cli --brag /path/to/your/git-repo -o ~/repo_showcase.mp4
```

---

## 10. Web Studio, REST API & Autonomous Agents

### Option 10.1: Local Web Studio Dashboard (Port 7860)
Launch the interactive browser UI to storyboard, preview scenes, adjust pacing, and inspect video renders:
```bash
python3 -m iram_video.cli --serve --port 7860
```
Open in browser: `http://localhost:7860`

### Option 10.2: Decoupled FastAPI REST Worker (Port 8000)
Launch the background asynchronous task queue server with SQLite durability:
```bash
python3 -m iram_video.cli --api --api-port 8000
```
* **Health Check**: `GET http://localhost:8000/api/v2/health`
* **Submit Task**: `POST http://localhost:8000/api/v2/generate`
* **Poll Task Status**: `GET http://localhost:8000/api/v2/tasks/{task_id}`
* **Instant Storyboard**: `POST http://localhost:8000/api/v2/draft`

### Option 10.3: Model Context Protocol (MCP Server)
Launch the JSON-RPC interface over stdio for LLMs, Claude Desktop, Antigravity, or Cursor:
```bash
python3 -m iram_video.cli --mcp
```

---

## 11. CLI Options & Argument Cheat Sheet

| Option | Values | Default | Description |
| :--- | :--- | :--- | :--- |
| `--real` | Flag | Off | Real documentary video mode using 1080p stock footage & real B-roll |
| `--shorts` | Flag | Off | Formats for 9:16 vertical (1080x1920) under 45 seconds |
| `--subtitles` | Flag | Off | Burns dynamic kinetic subtitles on center screen |
| `--lang` | `auto`, `en`, `ta` | `auto` | Language selection (`ta` triggers full Tamil screenplay, voice, and font) |
| `--voice` | `aria`, `christopher`, `jenny`, `valluvar`, `pallavi` | Auto | Voice persona (English: `aria`/`christopher`; Tamil: `valluvar`/`pallavi`) |
| `--music` | `energetic`, `cinematic`, `acoustic`, `documentary`, `lofi`, `tech`, `ambient`, `none` | `auto` | Background music mood |
| `--bg-music` | Path to audio (`.mp3`, `.wav`) | None | Custom external soundtrack or vocal song file |
| `--music-volume`| `0.0` to `1.0` | `0.20` | Music volume ducking level underneath speech |
| `--cinema` | Flag | Off | Hollywood trailer mode (24 FPS, 2.39:1 letterbox, 35mm grain, BRAAMs) |
| `--film` | Flag | Off | Animated feature film with multi-character dialogue engine |
| `--cast` | `nova,unit-7`, `ferris,gopher` | `nova,unit-7` | Animated character cast pairing |
| `--4k` | Flag | Off | UHD 3840x2160 rendering |
| `--template` | `explainer`, `tutorial`, `listicle`, `comparison`, `news`, `promo`, `podcast` | None | Directorial structure template |
| `--transition` | `fade`, `dissolve`, `wipeleft`, `wiperight`, `slideleft`, `slideright`, `cut` | `fade` | Transition between scenes |
| `--grade` | `clean`, `documentary`, `cinematic`, `vintage`, `noir`, `vibrant`, `none` | `clean` | Color grading (`clean` = 100% original camera colors) |
| `--subtitle-palette` | `gold`, `hormozi`, `neon-cyan`, `fire-red`, `purple`, `white` | `hormozi` | Subtitle text styling & keyword accent colors |
| `-o`, `--output` | File path (`.mp4`) | `./<slug>.mp4` | Master output video destination |
