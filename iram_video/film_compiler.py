import math
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Tuple
from PIL import Image, ImageDraw

from .environments import EnvironmentRenderer
from .characters import CharacterRenderer
from .renderer import get_fonts, draw_mixed_line, wrap_text
from .voice import VoiceSynthesizer
from .audio_synth import synthesize_mood_track

class FilmCompiler:
    """Compiles multi-character animated short films and feature films."""

    def __init__(self, work_dir: Path, language: str = "en"):
        self.work_dir = work_dir
        self.language = language
        self.shots_dir = work_dir / "film_shots"
        self.shots_dir.mkdir(parents=True, exist_ok=True)
        self.sprites_dir = work_dir / "film_sprites"
        self.sprites_dir.mkdir(parents=True, exist_ok=True)

    def _prepare_character_sprites(self, char_name: str, prefix: str):
        """Prepares animated mouth-flapping sprite frames for a character."""
        mouths = [0.0, 0.45, 0.85, 0.5, 0.15, 0.0]
        for i, mouth in enumerate(mouths):
            eye = "blink" if i == 4 else ("happy" if i in [2, 3] else "normal")
            bob = int(math.sin(i * 1.05) * 6)
            img = CharacterRenderer.render_character(
                char_name,
                w=340,
                h=440,
                mouth_open=mouth,
                eye_state=eye,
                pointing=(i in [1, 2]),
                bob_offset=bob
            )
            img.save(self.sprites_dir / f"{prefix}_{i:02d}.png")

        # Also prepare idle frame
        idle = CharacterRenderer.render_character(
            char_name,
            w=340,
            h=440,
            mouth_open=0.0,
            eye_state="normal",
            pointing=False,
            bob_offset=0
        )
        idle.save(self.sprites_dir / f"{prefix}_idle.png")

    def render_dialogue_shot(
        self,
        scene: Dict[str, Any],
        line_idx: int,
        speaker: str,
        text: str,
        audio_file: Path,
        duration: float,
        char1_info: Dict[str, Any],
        char2_info: Dict[str, Any]
    ) -> Path:
        """Renders an individual dialogue shot with talking character, listening character, and cinema subtitles."""
        out_shot = self.shots_dir / f"{scene.get('act_title', 'act')[:8]}_line_{line_idx:02d}.mp4"

        setting_name = scene.get("setting", "cyberpunk_city")
        bg_img = EnvironmentRenderer.render_set(setting_name, 1920, 1080)

        # Determine who is speaking
        is_char1_speaking = (speaker.lower() == char1_info.get("name", "").lower())

        # Left character (Char 1, facing right)
        char1_type = char1_info.get("character_type", "presenter")
        # Right character (Char 2, facing left)
        char2_type = char2_info.get("character_type", "robot")

        if is_char1_speaking:
            # Char 2 is idle on the right
            char2_idle = Image.open(self.sprites_dir / "c2_idle.png").transpose(Image.FLIP_LEFT_RIGHT)
            bg_img.paste(char2_idle, (1320, 540), char2_idle)
        else:
            # Char 1 is idle on the left
            char1_idle = Image.open(self.sprites_dir / "c1_idle.png")
            bg_img.paste(char1_idle, (260, 520), char1_idle)

        # Draw Cinema Letterbox bars (2.39:1 Hollywood Scope)
        draw = ImageDraw.Draw(bg_img)
        draw.rectangle([(0, 0), (1920, 138)], fill=(0, 0, 0, 255))
        draw.rectangle([(0, 942), (1920, 1080)], fill=(0, 0, 0, 255))

        # Act & Scene Header in top letterbox
        act_title = scene.get("act_title", "ACT I")
        loc_str = scene.get("time_and_place", "Station Sector — 03:00")
        fta_act, fen_act = get_fonts(24, bold=True)
        draw_mixed_line(draw, 70, 48, act_title, (255, 255, 255), fta_act, fen_act)
        fta_loc, fen_loc = get_fonts(16, bold=False)
        draw_mixed_line(draw, 70, 84, loc_str, (130, 165, 210), fta_loc, fen_loc)

        # Cinema Subtitle in bottom letterbox
        tag_color = (0, 229, 255, 255) if is_char1_speaking else (255, 170, 0, 255)
        speaker_tag = f"{speaker.upper()}: "
        fta_sub, fen_sub = get_fonts(26, bold=True)

        sw = draw.textlength(speaker_tag, font=fen_sub)
        wrapped_line = wrap_text(f'"{text}"', fta_sub, fen_sub, 1700 - int(sw), draw)

        sy = 968
        for i, wl in enumerate(wrapped_line[:2]):
            if i == 0:
                draw.text((80, sy), speaker_tag, fill=tag_color, font=fen_sub)
                draw_mixed_line(draw, 80 + int(sw), sy, wl, (255, 255, 255), fta_sub, fen_sub)
            else:
                draw_mixed_line(draw, 80 + int(sw), sy, wl, (255, 255, 255), fta_sub, fen_sub)
            sy += 36

        base_frame_path = self.work_dir / f"frame_{scene.get('act_title', 'act')[:8]}_{line_idx:02d}.png"
        bg_img.save(base_frame_path)

        # Animated Talking Character Sprite Input
        active_prefix = "c1" if is_char1_speaking else "c2"
        active_pos = "260:520" if is_char1_speaking else "1320:540"

        # If char2 is speaking, flip the animated sprite frames on the fly in ffmpeg: [1:v]hflip[c_flip]
        if is_char1_speaking:
            sprite_chain = f"[v_bg][1:v]overlay={active_pos}[v_comp]"
        else:
            sprite_chain = f"[1:v]hflip[c_flip];[v_bg][c_flip]overlay={active_pos}[v_comp]"

        d_frames = int(duration * 24) + 48
        fc = (
            f"[0:v]zoompan=z='min(zoom+0.0007,1.10)':d={d_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=24[v_bg];"
            f"{sprite_chain};"
            f"[v_comp]colorbalance=rs=0.08:gs=-0.04:bs=-0.08:rm=-0.04:gm=0.0:bm=0.12:rh=-0.04:gh=0.04:bh=0.18,noise=alls=11:allf=t+u[vfinal]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-framerate", "24", "-i", str(base_frame_path),
            "-stream_loop", "-1", "-framerate", "8", "-i", str(self.sprites_dir / f"{active_prefix}_%02d.png"),
            "-i", str(audio_file),
            "-filter_complex", fc,
            "-map", "[vfinal]",
            "-map", "2:a",
            "-af", "bass=g=3:f=110,equalizer=f=3200:t=q:w=1:g=2",
            "-c:v", "libx264", "-preset", "veryfast",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-t", f"{duration:.3f}",
            str(out_shot)
        ]

        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return out_shot

    def render_credits_sequence(self, film_title: str, credits: List[str], closing_quote: str, out_path: Path, duration: float = 8.0) -> Path:
        """Renders cinematic end credits scroll."""
        img = Image.new("RGBA", (1920, 1080), (6, 8, 14, 255))
        draw = ImageDraw.Draw(img)

        # Starfield
        import random
        rng = random.Random(999)
        for _ in range(120):
            sx, sy = rng.randint(0, 1920), rng.randint(0, 1080)
            draw.ellipse([(sx, sy), (sx + 2, sy + 2)], fill=(200, 220, 255, rng.randint(80, 200)))

        # Letterbox bars
        draw.rectangle([(0, 0), (1920, 138)], fill=(0, 0, 0, 255))
        draw.rectangle([(0, 942), (1920, 1080)], fill=(0, 0, 0, 255))

        # Centered Film Title
        fta_t, fen_t = get_fonts(48, bold=True)
        tw = draw.textlength(film_title, font=fen_t)
        draw.text(((1920 - tw) / 2, 220), film_title, fill=(0, 229, 255, 255), font=fen_t)

        # Closing philosophical quote
        if closing_quote:
            fta_q, fen_q = get_fonts(22, bold=False)
            qw = draw.textlength(f'"{closing_quote}"', font=fen_q)
            draw.text(((1920 - qw) / 2, 300), f'"{closing_quote}"', fill=(255, 215, 0, 230), font=fen_q)

        draw.line([(600, 360), (1320, 360)], fill=(0, 229, 255, 120), width=2)

        # Credits Roll
        fta_c, fen_c = get_fonts(22, bold=True)
        cy = 410
        for line in credits[:6]:
            lw = draw.textlength(line, font=fen_c)
            draw.text(((1920 - lw) / 2, cy), line, fill=(210, 225, 245, 230), font=fen_c)
            cy += 48

        frame_file = self.work_dir / "credits_frame.png"
        img.save(frame_file)

        fc = f"zoompan=z='min(zoom+0.0005,1.06)':d=192:s=1920x1080:fps=24,fade=t=in:st=0:d=1.0,fade=t=out:st={duration-1.0:.2f}:d=1.0"
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-framerate", "24", "-i", str(frame_file),
            "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-vf", fc,
            "-c:v", "libx264", "-preset", "veryfast",
            "-c:a", "aac", "-pix_fmt", "yuv420p",
            "-t", f"{duration:.3f}",
            str(out_path)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return out_path

    def compile_film(self, screenplay: Dict[str, Any], output_path: Path):
        """Orchestrates full feature film compilation across all acts and credits."""
        film_title = screenplay.get("film_title", "FEATURE FILM")
        cast = screenplay.get("cast", [
            {"name": "Nova", "role": "Architect", "character_type": "presenter", "voice_key": "female"},
            {"name": "Unit-7", "role": "Core", "character_type": "robot", "voice_key": "male"}
        ])
        char1_info = cast[0]
        char2_info = cast[1] if len(cast) > 1 else {"name": "Bot", "character_type": "robot", "voice_key": "male"}

        # Prepare character animated sprites
        self._prepare_character_sprites(char1_info.get("character_type", "presenter"), "c1")
        self._prepare_character_sprites(char2_info.get("character_type", "robot"), "c2")

        # Voice synthesizers for dialogue
        is_tamil = self.language.lower() in ["ta", "tamil"]
        v1_key = "pallavi" if is_tamil else "aria"
        v2_key = "valluvar" if is_tamil else "christopher"
        synth_c1 = VoiceSynthesizer(voice_key=v1_key, language=self.language, rate="-2%")
        synth_c2 = VoiceSynthesizer(voice_key=v2_key, language=self.language, rate="-2%")

        scenes = screenplay.get("scenes", [])
        shot_clips = []
        total_film_duration = 0.0

        for scene_idx, scene in enumerate(scenes):
            dialogue_lines = scene.get("dialogue", [])
            for line_idx, d in enumerate(dialogue_lines):
                speaker = d.get("speaker", "Character")
                text = d.get("line", "")

                is_char1 = (speaker.lower() == char1_info.get("name", "").lower())
                synth = synth_c1 if is_char1 else synth_c2

                line_audio = self.work_dir / f"audio_s{scene_idx}_l{line_idx}.mp3"
                duration = synth.synthesize_line(text, line_audio)
                total_film_duration += duration

                shot_clip = self.render_dialogue_shot(
                    scene=scene,
                    line_idx=line_idx,
                    speaker=speaker,
                    text=text,
                    audio_file=line_audio,
                    duration=duration,
                    char1_info=char1_info,
                    char2_info=char2_info
                )
                shot_clips.append(shot_clip)

        # Render End Credits
        credits = screenplay.get("credits", [
            "DIRECTED BY: IRAM AI Studios",
            f"STARRING: {char1_info.get('name', 'Nova')} & {char2_info.get('name', 'Unit-7')}",
            "MUSIC: Hans Zimmer Synthesizer Suite",
            "EXECUTIVE PRODUCER: apravint"
        ])
        closing_quote = screenplay.get("closing_quote", "")
        credits_clip = self.shots_dir / "end_credits.mp4"
        self.render_credits_sequence(film_title, credits, closing_quote, credits_clip, duration=7.5)
        shot_clips.append(credits_clip)
        total_film_duration += 7.5

        # Concat all shots
        concat_txt = self.work_dir / "film_concat.txt"
        with open(concat_txt, "w") as f:
            for sc in shot_clips:
                f.write(f"file '{sc.resolve()}'\n")

        raw_concat = self.work_dir / "film_raw.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_txt), "-c", "copy", str(raw_concat)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Synthesize Full Feature Soundtrack (Trailer score with BRAAMs)
        soundtrack_wav = self.work_dir / "film_soundtrack.wav"
        synthesize_mood_track("trailer", total_film_duration + 8.0, soundtrack_wav)

        # Master Film Mix with dialogue ducking
        fc = (
            "[0:a]volume=1.0[dialogue];"
            "[1:a]volume=0.22[score];"
            "[dialogue][score]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )
        cmd_master = [
            "ffmpeg", "-y",
            "-i", str(raw_concat),
            "-i", str(soundtrack_wav),
            "-filter_complex", fc,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "256k",
            "-movflags", "+faststart",
            str(output_path)
        ]
        subprocess.run(cmd_master, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
