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
    # Handle both English and Tamil transliterated slugs
    clean = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip().lower()
    slug = re.sub(r"[-\s]+", "_", clean)[:40]
    return slug or "iram_video_output"

def main():
    parser = argparse.ArgumentParser(
        prog="iram-video",
        description="Universal Prompt-to-Video Engine (English & Tamil) powered by Google Gemini, Edge TTS, PIL & FFMPEG."
    )
    parser.add_argument("prompt", help="Topic, brief, or prompt for the video (English or தமிழ்)")
    parser.add_argument("-o", "--output", help="Output MP4 file path (default: ./<slug>.mp4)")
    parser.add_argument("--lang", default="auto", choices=["auto", "en", "ta", "tamil", "english"], help="Language: 'en' for English, 'ta' for Tamil, 'auto' for auto-detection (default: auto)")
    parser.add_argument("--voice", default="default", help="Voice persona ('aria', 'christopher', 'jenny', 'pallavi' (Tamil female), 'valluvar' (Tamil male), etc.)")
    parser.add_argument("--scenes", type=int, default=None, help="Desired scene count (default: auto)")
    parser.add_argument("--music", default="cyber", choices=["cyber", "lofi", "tech", "ambient", "none"], help="Background music mood (default: cyber)")
    parser.add_argument("--no-thumbnail", action="store_true", help="Skip YouTube thumbnail generation")
    parser.add_argument("--style", default=None, help="Style hint for the director (e.g. 'dark mode', 'educational', 'fast-paced')")

    args = parser.parse_args()

    # Detect language
    lang = args.lang.lower()
    if lang == "auto":
        lang = "ta" if is_tamil_text(args.prompt) else "en"
    elif lang in ["tamil", "ta"]:
        lang = "ta"
    else:
        lang = "en"

    slug = slugify(args.prompt)
    output_mp4 = Path(args.output).resolve() if args.output else Path(f"./{slug}.mp4").resolve()
    thumb_png = output_mp4.with_suffix(".png")
    meta_txt = output_mp4.with_suffix(".txt")

    lang_display = "தமிழ் (Tamil)" if lang == "ta" else "English"
    print(f"\n🎬 [IRAM VIDEO ENGINE] Initializing Video Generation Pipeline")
    print(f"► Prompt: \"{args.prompt}\"")
    print(f"► Language: {lang_display} | Music Mood: {args.music}")
    print(f"► Output Target: {output_mp4}\n")

    with tempfile.TemporaryDirectory(prefix="iram_video_") as tmpdir:
        work_dir = Path(tmpdir)
        audio_dir = work_dir / "audio"
        slides_dir = work_dir / "slides"
        slides_dir.mkdir(parents=True, exist_ok=True)

        # 1. Direct with Google Gemini (Bilingual)
        print(f"🧠 [1/5] Directing screenplay with Google Gemini 3.8 Flash ({lang_display})...")
        director = Director()
        try:
            screenplay = director.direct(args.prompt, scene_count=args.scenes, style_hint=args.style, language=lang)
        except Exception as e:
            print(f"❌ Failed to direct screenplay with Google Gemini: {e}")
            sys.exit(1)

        video_title = screenplay.get("video_title", args.prompt[:60])
        scenes = screenplay.get("scenes", [])
        theme_palette = screenplay.get("theme_palette", {})
        print(f"✓ Screenplay ready: \"{video_title}\" ({len(scenes)} scenes)")

        # 2. Voiceover Synthesis (Auto-selects Tamil or English neural studio voice)
        print(f"🎙️  [2/5] Synthesizing neural voiceover ({lang_display})...")
        voice_synth = VoiceSynthesizer(voice_key=args.voice, language=lang)
        scenes = voice_synth.synthesize(scenes, audio_dir)
        total_duration = sum(s["duration"] for s in scenes)
        print(f"✓ Voiceover complete using voice '{voice_synth.voice}': {total_duration:.1f}s total duration")

        # 3. Slide Frame Rendering (Supports Tamil Unicode + English)
        print(f"🎨 [3/5] Rendering 1080p graphic slide frames ({lang_display} typography)...")
        renderer = SlideRenderer(theme=theme_palette)
        slide_paths = []
        for i, scene in enumerate(scenes):
            out_slide = slides_dir / f"{scene['id']}.png"
            renderer.render_scene(scene, video_title, out_slide)
            slide_paths.append(out_slide)
        print(f"✓ Rendered {len(slide_paths)} 1080p slide frames")

        # 4. Background Music Synthesis
        bg_music_wav = work_dir / "bg_music.wav"
        if args.music != "none":
            print(f"🎵 [4/5] Synthesizing '{args.music}' ambient mood track...")
            synthesize_mood_track(args.music, total_duration + 5.0, bg_music_wav)
            print("✓ Mood soundtrack ready")
        else:
            bg_music_wav = None

        # 5. Master Video Compilation
        print("⚙️  [5/5] Compiling master 1080p MP4 with FFMPEG...")
        compiler = VideoCompiler(work_dir)
        compiler.compile(scenes, slide_paths, bg_music_wav, output_mp4)
        print(f"🎉 MASTER VIDEO GENERATED: {output_mp4}")

        # 6. Thumbnail Generation
        if not args.no_thumbnail:
            bullets = [s.get("heading", "") for s in scenes]
            generate_thumbnail(video_title, bullets, theme_palette, thumb_png)
            print(f"🖼️  YOUTUBE THUMBNAIL: {thumb_png}")

        # 7. Metadata Export
        yt_meta = screenplay.get("youtube_metadata", {})
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
            f.write(f"\nTAGS:\n{', '.join(yt_meta.get('tags', []))}\n")
        print(f"📋 YOUTUBE METADATA: {meta_txt}")

        print("\n" + "="*60)
        print(f"✅ Video creation complete ({lang_display})!")
        print(f"• Video:     {output_mp4} ({total_duration:.1f}s)")
        if not args.no_thumbnail:
            print(f"• Thumbnail: {thumb_png}")
        print(f"• Metadata:  {meta_txt}")
        print("="*60 + "\n")

if __name__ == "__main__":
    main()
