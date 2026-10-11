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

def slugify(text: str) -> str:
    clean = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip().lower()
    slug = re.sub(r"[-\s]+", "_", clean)[:40]
    return slug or "iram_video_output"

def main():
    parser = argparse.ArgumentParser(
        prog="iram-video",
        description="Universal Prompt-to-Video Engine (Cinema, Animated Characters, Shorts & Landscape, English & தமிழ்)."
    )
    parser.add_argument("prompt", help="Topic, brief, or prompt for the video (English or தமிழ்)")
    parser.add_argument("-o", "--output", help="Output MP4 file path (default: ./<slug>.mp4)")
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

    # Detect language
    lang = args.lang.lower()
    if lang == "auto":
        lang = "ta" if is_tamil_text(args.prompt) else "en"
    elif lang in ["tamil", "ta"]:
        lang = "ta"
    else:
        lang = "en"

    is_shorts = args.shorts
    is_cinema = args.cinema

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

    # Music default for cinema
    music_mood = args.music
    if is_cinema and music_mood == "cyber":
        music_mood = "trailer"

    if is_cinema:
        format_label = "Hollywood Cinema Trailer (24 FPS, 2.39:1 Scope)" if not is_shorts else "Vertical Cinematic Shorts (24 FPS, Scope Bars)"
    elif is_shorts:
        format_label = "YouTube Shorts (Vertical 9:16, 1080x1920)"
    else:
        format_label = "Landscape (16:9, 1920x1080)"

    slug = slugify(args.prompt)
    if is_shorts and not slug.endswith("_shorts"):
        slug += "_shorts"
    if is_cinema and not slug.endswith("_cinema"):
        slug += "_cinema"

    output_mp4 = Path(args.output).resolve() if args.output else Path(f"./{slug}.mp4").resolve()
    thumb_png = output_mp4.with_suffix(".png")
    meta_txt = output_mp4.with_suffix(".txt")

    lang_display = "தமிழ் (Tamil)" if lang == "ta" else "English"
    char_display = f" | Mascot: {character}" if character else ""
    print(f"\n🎬 [IRAM VIDEO ENGINE] Initializing Video Generation Pipeline")
    print(f"► Prompt: \"{args.prompt}\"")
    print(f"► Format: {format_label}{char_display}")
    print(f"► Language: {lang_display} | Music Mood: {music_mood}")
    print(f"► Output Target: {output_mp4}\n")

    with tempfile.TemporaryDirectory(prefix="iram_video_") as tmpdir:
        work_dir = Path(tmpdir)
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
        compiler.compile(scenes, slide_paths, bg_music_wav, output_mp4)
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
