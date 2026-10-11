import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

from .director import Director
from .voice import VoiceSynthesizer
from .renderer import SlideRenderer, is_tamil_text
from .audio_synth import synthesize_mood_track
from .compiler import VideoCompiler
from .thumbnail import generate_thumbnail
from .film_director import FilmDirector
from .film_compiler import FilmCompiler
from .server import start_server

def slugify(text: str) -> str:
    clean = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip().lower()
    slug = re.sub(r"[-\s]+", "_", clean)[:40]
    return slug or "iram_video_output"

def load_prompt_from_json(json_path: Path):
    """Extracts a rich video directing prompt and style hint from a structured JSON document."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        names = [item.get("name", "") for item in data[:8] if isinstance(item, dict)]
        title = json_path.stem.replace("-", " ").title()
        prompt = f"Comprehensive breakdown of {title}: Featuring {', '.join(names)}"
        style = f"Educational tech showcase reviewing {len(data)} tools"
        return prompt, style

    title = data.get("title", json_path.stem.replace("-", " ").title())
    desc = data.get("description", "")
    workflow = data.get("workflow_stages") or data.get("architecture_pipeline") or data.get("business_logic") or ""

    items = []
    if "skills" in data and isinstance(data["skills"], list):
        items = [s.get("name", "") for s in data["skills"][:8]]
    elif "categories" in data and isinstance(data["categories"], dict):
        for cat, tool_list in data["categories"].items():
            if isinstance(tool_list, list):
                items.extend([t.get("name", "") for t in tool_list[:3] if isinstance(t, dict)])
    elif "offers" in data and isinstance(data["offers"], list):
        items = [o.get("name", "") for o in data["offers"][:5]]

    items_str = f" Highlights: {', '.join(items[:8])}." if items else ""
    flow_str = f" Pipeline: {workflow}." if workflow else ""
    prompt = f"{title}. {desc}{items_str}{flow_str}"
    style = f"Technical and architectural deep-dive based on {json_path.name}"
    return prompt, style

def main():
    parser = argparse.ArgumentParser(
        prog="iram-video",
        description="Universal Film & Video Engine (Animation Feature Films, Cinema Trailers, Animated Characters, Shorts & Landscape, English & தமிழ்)."
    )
    parser.add_argument("prompt", nargs="?", default="", help="Topic, brief, or screenplay premise (English or தமிழ்)")
    parser.add_argument("--from-json", default=None, help="Directly ingest a structured JSON document or stack blueprint (e.g. software-factory-skills.json)")
    parser.add_argument("--serve", action="store_true", help="Launch the local Web Studio dashboard server (default port 7860)")
    parser.add_argument("--port", type=int, default=7860, help="Web Studio port (default: 7860)")
    parser.add_argument("-o", "--output", help="Output MP4 file path (default: ./<slug>.mp4)")
    parser.add_argument("--film", "--feature", dest="film", action="store_true", help="Generate as full Multi-Character Animated Feature Film with dialogue, procedural sets, score & rolling end credits")
    parser.add_argument("--cast", default=None, help="Cast preference (e.g. 'nova,unit-7' or 'ferris,gopher')")
    parser.add_argument("--shorts", action="store_true", help="Generate as vertical YouTube Shorts (9:16, 1080x1920, < 60s)")
    parser.add_argument("--cinema", "--movie", dest="cinema", action="store_true", help="Generate as Hollywood-grade cinema trailer (24 FPS, 2.39:1 letterbox, 35mm grain, color grade, Inception BRAAMs)")
    parser.add_argument("--character", default="none", choices=["none", "auto", "robot", "presenter", "ferris", "gopher"], help="Add animated character mascot ('robot', 'presenter', 'ferris', 'gopher', 'auto')")
    parser.add_argument("--lang", default="auto", choices=["auto", "en", "ta", "tamil", "english"], help="Language: 'en' for English, 'ta' for Tamil, 'auto' for auto-detection (default: auto)")
    parser.add_argument("--voice", default="default", help="Voice persona ('aria', 'christopher', 'jenny', 'pallavi' [Tamil female], 'valluvar' [Tamil male], etc.)")
    parser.add_argument("--scenes", type=int, default=None, help="Desired scene count (default: auto)")
    parser.add_argument("--music", default="cyber", choices=["cyber", "lofi", "tech", "ambient", "trailer", "cinematic", "none"], help="Background music mood (default: cyber or trailer if --cinema)")
    parser.add_argument("--no-thumbnail", action="store_true", help="Skip thumbnail generation")
    parser.add_argument("--style", default=None, help="Style hint for the director (e.g. 'dark mode', 'educational', 'fast-paced', 'epic blockbuster')")

    args = parser.parse_args()

    if args.serve or (len(sys.argv) > 1 and sys.argv[1] == "serve"):
        start_server(args.port)
        return

    # Ingest from JSON document if provided
    if args.from_json:
        json_file = Path(args.from_json).resolve()
        if not json_file.exists():
            print(f"❌ JSON document not found: {json_file}")
            sys.exit(1)
        j_prompt, j_style = load_prompt_from_json(json_file)
        if not args.prompt:
            args.prompt = j_prompt
        if not args.style:
            args.style = j_style
        print(f"📄 [JSON INGESTION] Loaded blueprint: \"{json_file.name}\"")

    if not args.prompt:
        parser.print_help()
        sys.exit(1)

    # Detect language
    lang = args.lang.lower()
    if lang == "auto":
        lang = "ta" if is_tamil_text(args.prompt) else "en"
    elif lang in ["tamil", "ta"]:
        lang = "ta"
    else:
        lang = "en"

    is_film = args.film
    is_shorts = args.shorts
    is_cinema = args.cinema or is_film

    # Character selection
    character = args.character
    if character == "auto":
        p_low = args.prompt.lower()
        if "rust" in p_low:
            character = "ferris"
        elif "go" in p_low or "golang" in p_low:
            character = "gopher"
        elif "girl" in p_low or "host" in p_low or "presenter" in p_low:
            character = "presenter"
        else:
            character = "robot"
    elif character == "none":
        character = None

    # Music default for cinema / film
    music_mood = args.music
    if (is_cinema or is_film) and music_mood == "cyber":
        music_mood = "trailer"

    if is_film:
        format_label = "Animated Feature Film (Multi-Character Dialogue & Procedural Sets)"
    elif is_cinema:
        format_label = "Hollywood Cinema Trailer (24 FPS, 2.39:1 Scope)" if not is_shorts else "Vertical Cinematic Shorts (24 FPS, Scope Bars)"
    elif is_shorts:
        format_label = "YouTube Shorts (Vertical 9:16, 1080x1920)"
    else:
        format_label = "Landscape (16:9, 1920x1080)"

    slug = slugify(args.prompt)
    if is_shorts and not slug.endswith("_shorts"):
        slug += "_shorts"
    if is_cinema and not slug.endswith("_cinema") and not is_film:
        slug += "_cinema"
    if is_film and not slug.endswith("_film"):
        slug += "_film"

    output_mp4 = Path(args.output).resolve() if args.output else Path(f"./{slug}.mp4").resolve()
    thumb_png = output_mp4.with_suffix(".png")
    meta_txt = output_mp4.with_suffix(".txt")

    lang_display = "தமிழ் (Tamil)" if lang == "ta" else "English"
    char_display = f" | Mascot: {character}" if character else ""
    print(f"\n🎬 [IRAM FILM STUDIO] Initializing Video Generation Pipeline")
    print(f"► Premise: \"{args.prompt}\"")
    print(f"► Format: {format_label}{char_display}")
    print(f"► Language: {lang_display} | Score: {music_mood}")
    print(f"► Master Output: {output_mp4}\n")

    with tempfile.TemporaryDirectory(prefix="iram_video_") as tmpdir:
        work_dir = Path(tmpdir)

        if is_film:
            # --- ANIMATED FEATURE FILM PIPELINE ---
            print(f"🧠 [1/4] Screenwriting & Directing Animated Feature Film...")
            film_director = FilmDirector()
            try:
                screenplay = film_director.direct_film(
                    args.prompt,
                    scene_count=args.scenes or 3,
                    language=lang,
                    style_hint=args.style,
                    cast_hint=args.cast
                )
            except Exception as e:
                print(f"❌ Screenplay direction failed: {e}")
                sys.exit(1)

            film_title = screenplay.get("film_title", args.prompt[:60])
            cast = screenplay.get("cast", [])
            print(f"✓ Feature Screenplay Written: \"{film_title}\" ({len(screenplay.get('scenes', []))} Acts)")
            print(f"🎭 Cast: {', '.join(c.get('name', 'Actor') + ' as ' + c.get('role', 'Role') for c in cast)}")

            print(f"⚙️  [2/4] Recording multi-character dialogue & staging procedural sets...")
            compiler = FilmCompiler(work_dir, language=lang)
            print(f"🎥 [3/4] Compiling 24 FPS cinema shots with animated lip-sync & 35mm film grain...")
            compiler.compile_film(screenplay, output_mp4)
            print(f"🎉 MASTER FEATURE FILM GENERATED: {output_mp4}")

            print(f"🖼️  [4/4] Designing theatrical film poster & metadata...")
            if not args.no_thumbnail:
                act_titles = [s.get("act_title", "") for s in screenplay.get("scenes", [])]
                primary_char = cast[0].get("character_type", "presenter") if cast else "presenter"
                generate_thumbnail(
                    film_title,
                    act_titles,
                    {"bg": [8, 10, 20], "accent": [0, 229, 255], "secondary": [168, 85, 247]},
                    thumb_png,
                    is_cinema=True,
                    character=primary_char
                )
                print(f"🖼️  THEATRICAL POSTER: {thumb_png}")

            yt_meta = screenplay.get("youtube_metadata", {})
            with open(meta_txt, "w") as f:
                f.write(f"FILM TITLE:\n{film_title}\n\n")
                f.write(f"GENRE:\n{screenplay.get('genre', 'Sci-Fi Animation')}\n\n")
                f.write(f"SYNOPSIS:\n{yt_meta.get('description', '')}\n\n")
                f.write("CAST & ROLES:\n")
                for c in cast:
                    f.write(f"• {c.get('name')}: {c.get('role')} (Rig: {c.get('character_type')})\n")
                f.write("\nACTS & SCENES:\n")
                for s in screenplay.get("scenes", []):
                    f.write(f"• {s.get('act_title')} [{s.get('setting')}] — {s.get('time_and_place')}\n")
                f.write(f"\nCLOSING QUOTE:\n\"{screenplay.get('closing_quote', '')}\"\n")
                f.write(f"\nCREDITS:\n{chr(10).join(screenplay.get('credits', []))}\n")
                f.write(f"\nTAGS:\n{', '.join(yt_meta.get('tags', []))}\n")
            print(f"📋 FILM ARCHIVE & METADATA: {meta_txt}")

            print("\n" + "=" * 60)
            print(f"🎬 Feature Film Production Complete!")
            print(f"• Movie Master: {output_mp4}")
            if not args.no_thumbnail:
                print(f"• Film Poster:  {thumb_png}")
            print(f"• Screenplay:   {meta_txt}")
            print("=" * 60 + "\n")
            return

        # --- STANDARD VIDEO & CINEMA TRAILER PIPELINE ---
        audio_dir = work_dir / "audio"
        slides_dir = work_dir / "slides"
        slides_dir.mkdir(parents=True, exist_ok=True)

        # 1. Direct with Google Gemini (Shorts-aware & Bilingual)
        print(f"🧠 [1/5] Directing screenplay with Google Gemini 3.8 Flash ({format_label})...")
        director = Director()
        try:
            screenplay = director.direct(
                args.prompt,
                scene_count=args.scenes,
                style_hint=args.style,
                language=lang,
                is_shorts=is_shorts,
                is_cinema=is_cinema,
                character=character
            )
        except Exception as e:
            print(f"❌ Failed to direct screenplay with Google Gemini: {e}")
            sys.exit(1)

        video_title = screenplay.get("video_title", args.prompt[:60])
        if is_shorts and "#Shorts" not in video_title and "#shorts" not in video_title:
            video_title += " #Shorts"

        scenes = screenplay.get("scenes", [])
        theme_palette = screenplay.get("theme_palette", {})
        print(f"✓ Screenplay ready: \"{video_title}\" ({len(scenes)} scenes)")

        # 2. Voiceover Synthesis (Snappy pacing for Shorts, deep pacing for Cinema)
        rate = "+4%" if is_shorts else ("-2%" if is_cinema else "+2%")
        print(f"🎙️  [2/5] Synthesizing neural voiceover ({lang_display})...")
        voice_synth = VoiceSynthesizer(voice_key=args.voice, language=lang, rate=rate)
        scenes = voice_synth.synthesize(scenes, audio_dir)
        total_duration = sum(s["duration"] for s in scenes)
        print(f"✓ Voiceover complete using voice '{voice_synth.voice}': {total_duration:.1f}s total duration")

        # 3. Slide Frame Rendering (Vertical 9:16 or Landscape 16:9)
        dim_str = "1080x1920" if is_shorts else "1920x1080"
        print(f"🎨 [3/5] Rendering {dim_str} slide frames ({lang_display} typography)...")
        renderer = SlideRenderer(theme=theme_palette, is_shorts=is_shorts)
        slide_paths = []
        for i, scene in enumerate(scenes):
            out_slide = slides_dir / f"{scene['id']}.png"
            renderer.render_scene(scene, video_title, out_slide)
            slide_paths.append(out_slide)
        print(f"✓ Rendered {len(slide_paths)} {dim_str} slide frames")

        # 4. Background Music Synthesis
        bg_music_wav = work_dir / "bg_music.wav"
        if music_mood != "none":
            print(f"🎵 [4/5] Synthesizing '{music_mood}' soundtrack...")
            synthesize_mood_track(music_mood, total_duration + 5.0, bg_music_wav)
            print("✓ Soundtrack ready")
        else:
            bg_music_wav = None

        # 5. Master Video Compilation
        print(f"⚙️  [5/5] Compiling master {dim_str} MP4 with FFMPEG...")
        compiler = VideoCompiler(work_dir, is_cinema=is_cinema, is_shorts=is_shorts, character=character)
        compiler.compile(scenes, slide_paths, bg_music_wav, output_mp4, language=lang)
        print(f"🎉 MASTER VIDEO GENERATED: {output_mp4}")

        # 6. Thumbnail Generation
        if not args.no_thumbnail:
            bullets = [s.get("heading", "") for s in scenes]
            generate_thumbnail(video_title, bullets, theme_palette, thumb_png, is_shorts=is_shorts, is_cinema=is_cinema, character=character)
            print(f"🖼️  YOUTUBE THUMBNAIL: {thumb_png}")

        # 7. Metadata Export
        yt_meta = screenplay.get("youtube_metadata", {})
        tags = yt_meta.get("tags", [])
        if is_shorts and "Shorts" not in tags and "#Shorts" not in tags:
            tags.insert(0, "#Shorts")

        with open(meta_txt, "w") as f:
            f.write(f"TITLE:\n{video_title}\n\n")
            f.write(f"DESCRIPTION:\n{yt_meta.get('description', '')}\n\n")
            f.write("CHAPTERS:\n")
            curr_sec = 0.0
            for s in scenes:
                mins = int(curr_sec // 60)
                secs = int(curr_sec % 60)
                f.write(f"{mins}:{secs:02d} {s.get('heading', '')}\n")
                curr_sec += s["duration"]
            f.write(f"\nTAGS:\n{', '.join(tags)}\n")
        print(f"📋 YOUTUBE METADATA: {meta_txt}")

        print("\n" + "="*60)
        print(f"✅ Video creation complete ({format_label})!")
        print(f"• Video:     {output_mp4} ({total_duration:.1f}s)")
        if not args.no_thumbnail:
            print(f"• Thumbnail: {thumb_png}")
        print(f"• Metadata:  {meta_txt}")
        print("="*60 + "\n")

if __name__ == "__main__":
    main()
