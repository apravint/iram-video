import math
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from .characters import CharacterRenderer

class VideoCompiler:
    def __init__(self, work_dir: Path, is_cinema: bool = False, is_shorts: bool = False, character: Optional[str] = None):
        self.work_dir = work_dir
        self.is_cinema = is_cinema
        self.is_shorts = is_shorts
        self.character = character
        self.clips_dir = work_dir / "clips"
        self.clips_dir.mkdir(parents=True, exist_ok=True)
        self.sprites_dir = work_dir / "char_sprites"
        self.sprites_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare character sprites if requested
        self.has_character = bool(character and character.lower() not in ["none", "false"])
        if self.has_character:
            self._prepare_character_sprites()

    def _prepare_character_sprites(self):
        """Generates cycling animated sprite frames for the character mascot."""
        char_name = self.character or "robot"
        cw, ch = (320, 420) if self.is_shorts else (380, 480)
        
        mouth_sequence = [0.0, 0.4, 0.85, 0.5, 0.15, 0.0]
        for i, mouth in enumerate(mouth_sequence):
            eye = "blink" if i == 4 else ("happy" if i in [2, 3] else "normal")
            bob = int(math.sin(i * 1.05) * 8)
            img = CharacterRenderer.render_character(
                char_name,
                w=cw,
                h=ch,
                mouth_open=mouth,
                eye_state=eye,
                pointing=True,
                bob_offset=bob
            )
            img.save(self.sprites_dir / f"sprite_{i:02d}.png")

    def render_clip(self, scene: Dict[str, Any], slide_img: Path) -> Path:
        sid = scene["id"]
        duration = scene["duration"]
        audio_file = Path(scene["audio_file"])
        out_clip = self.clips_dir / f"{sid}.mp4"

        framerate = 24 if self.is_cinema else 30
        fade_out = max(0, duration - 0.4)

        # Build sequential filter graph
        fc_parts = []
        cur_v = "[0:v]"

        # 1. Base motion (Cinematic camera dolly push-in)
        if self.is_cinema:
            d_frames = int(duration * framerate) + 48
            if self.is_shorts:
                fc_parts.append(f"{cur_v}zoompan=z='min(zoom+0.0008,1.12)':d={d_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={framerate}[v_bg]")
            else:
                fc_parts.append(f"{cur_v}zoompan=z='min(zoom+0.0008,1.12)':d={d_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps={framerate}[v_bg]")
            cur_v = "[v_bg]"

        # 2. Character overlay
        inputs = [
            "-loop", "1",
            "-framerate", str(framerate),
            "-i", str(slide_img)
        ]

        if self.has_character:
            inputs.extend([
                "-stream_loop", "-1",
                "-framerate", "8",
                "-i", str(self.sprites_dir / "sprite_%02d.png")
            ])
            pos_x = 680 if self.is_shorts else 1500
            pos_y = 1440 if self.is_shorts else 540
            fc_parts.append(f"{cur_v}[1:v]overlay={pos_x}:{pos_y}[v_char]")
            cur_v = "[v_char]"

        # 3. Cinema post-processing: 2.39:1 Anamorphic letterbox, color grading & film grain
        post_filters = []
        if self.is_cinema:
            if not self.is_shorts:
                # Hollywood 2.39:1 scope bars (top and bottom 138px bars)
                post_filters.append("drawbox=y=0:h=138:color=black:t=fill")
                post_filters.append("drawbox=y=942:h=138:color=black:t=fill")
            else:
                # Scope accent bars for vertical video
                post_filters.append("drawbox=y=0:h=90:color=black:t=fill")
                post_filters.append("drawbox=y=1830:h=90:color=black:t=fill")

            # Teal & Orange cinematic color matrix
            post_filters.append("colorbalance=rs=0.08:gs=-0.04:bs=-0.08:rm=-0.04:gm=0.0:bm=0.12:rh=-0.04:gh=0.04:bh=0.18")
            # 35mm analog film grain
            post_filters.append("noise=alls=12:allf=t+u")

        # 4. Fade in/out
        post_filters.append(f"fade=t=in:st=0:d=0.35,fade=t=out:st={fade_out:.2f}:d=0.35")

        if post_filters:
            fc_parts.append(f"{cur_v}{','.join(post_filters)}[vfinal]")
            v_map = "[vfinal]"
        else:
            v_map = cur_v

        filter_complex = ";".join(fc_parts)

        # Voice processing (bass boost & cinematic room acoustics in cinema mode)
        af_opts = []
        if self.is_cinema:
            af_opts.extend([
                "-af", "bass=g=4:f=110,equalizer=f=3200:t=q:w=1:g=2,aecho=0.8:0.88:35:0.2"
            ])

        audio_idx = 2 if self.has_character else 1

        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-i", str(audio_file),
            "-filter_complex", filter_complex,
            "-map", v_map,
            "-map", f"{audio_idx}:a",
            *af_opts,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-t", f"{duration:.3f}",
            str(out_clip)
        ]

        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return out_clip

    def compile(self, scenes: List[Dict[str, Any]], slide_paths: List[Path], bg_music: Path, final_output: Path):
        clip_paths = []
        for scene, slide in zip(scenes, slide_paths):
            c = self.render_clip(scene, slide)
            clip_paths.append(c)

        # Write concat list
        concat_txt = self.work_dir / "concat_list.txt"
        with open(concat_txt, "w") as f:
            for cp in clip_paths:
                f.write(f"file '{cp.resolve()}'\n")

        raw_concat = self.work_dir / "raw_concat.mp4"
        cmd_cat = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_txt),
            "-c", "copy",
            str(raw_concat)
        ]
        subprocess.run(cmd_cat, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Mix background audio with ducking
        music_vol = 0.24 if self.is_cinema else 0.12
        if bg_music and bg_music.exists():
            fc = (
                f"[0:a]volume=1.0[voice];"
                f"[1:a]volume={music_vol:.2f}[bg];"
                f"[voice][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]"
            )
            cmd_mix = [
                "ffmpeg", "-y",
                "-i", str(raw_concat),
                "-i", str(bg_music),
                "-filter_complex", fc,
                "-map", "0:v",
                "-map", "[aout]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "256k",
                "-movflags", "+faststart",
                str(final_output)
            ]
        else:
            cmd_mix = [
                "ffmpeg", "-y",
                "-i", str(raw_concat),
                "-c", "copy",
                "-movflags", "+faststart",
                str(final_output)
            ]

        subprocess.run(cmd_mix, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
