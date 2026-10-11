import math
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

from .b_roll import MediaFetcher
from .audio_synth import synthesize_mood_track

class RealVideoCompiler:
    """Compiles realistic documentary-style YouTube videos with real B-roll footage and photography (no cyberpunk, no subtitles)."""

    def __init__(self, work_dir: Path, is_shorts: bool = False):
        self.work_dir = work_dir
        self.is_shorts = is_shorts
        self.broll_dir = work_dir / "broll_media"
        self.broll_dir.mkdir(parents=True, exist_ok=True)
        self.shots_dir = work_dir / "real_shots"
        self.shots_dir.mkdir(parents=True, exist_ok=True)
        self.w = 1080 if is_shorts else 1920
        self.h = 1920 if is_shorts else 1080

    def _render_single_shot(self, query: str, duration: float, audio_file: Path, out_shot: Path, scene_idx: int) -> Path:
        media_path = MediaFetcher.fetch_scene_broll(query, self.broll_dir, scene_idx)
        is_video = media_path.suffix.lower() in [".mp4", ".webm", ".mkv", ".mov"]

        if is_video:
            fc = (
                f"[0:v]scale={self.w}:{self.h}:force_original_aspect_ratio=increase,"
                f"crop={self.w}:{self.h},fps=30[v]"
            )
            cmd = [
                "ffmpeg", "-y",
                "-stream_loop", "-1", "-i", str(media_path),
                "-i", str(audio_file),
                "-filter_complex", fc,
                "-map", "[v]",
                "-map", "1:a",
                "-c:v", "libx264", "-preset", "veryfast",
                "-c:a", "aac", "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-t", f"{duration:.3f}",
                str(out_shot)
            ]
        else:
            d_frames = int(duration * 30) + 30
            sw, sh = (int(self.w * 1.3), int(self.h * 1.3))
            fc = (
                f"[0:v]scale={sw}:{sh}:force_original_aspect_ratio=increase,"
                f"crop={sw}:{sh},"
                f"zoompan=z='min(zoom+0.0004,1.08)':d={d_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={self.w}x{self.h}:fps=30,"
                f"fade=t=in:st=0:d=0.35,fade=t=out:st={max(0.1, duration - 0.35):.2f}:d=0.35[v]"
            )
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", str(media_path),
                "-i", str(audio_file),
                "-filter_complex", fc,
                "-map", "[v]",
                "-map", "1:a",
                "-c:v", "libx264", "-preset", "veryfast",
                "-c:a", "aac", "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-t", f"{duration:.3f}",
                str(out_shot)
            ]

        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return out_shot

    def render_shot(self, scene: Dict[str, Any], scene_idx: int) -> Path:
        duration = float(scene.get("duration", 4.0))
        audio_file = Path(scene["audio_file"])
        out_shot = self.shots_dir / f"shot_{scene_idx:02d}.mp4"

        # Extract rapid visual beats (cutting every 3.5 to 5.5 seconds for maximum engagement)
        beats = MediaFetcher.extract_scene_beats(scene, duration)

        if len(beats) <= 1:
            query = scene.get("search_query") or scene.get("heading") or "documentary landscape"
            return self._render_single_shot(query, duration, audio_file, out_shot, scene_idx)

        # Render each beat sub-clip with fresh real B-roll
        beat_clips = []
        for b_idx, beat in enumerate(beats):
            b_dur = float(beat["duration"])
            b_query = beat["query"]
            beat_clip_path = self.shots_dir / f"beat_{scene_idx:02d}_{b_idx:02d}.mp4"

            media_path = MediaFetcher.fetch_media_for_beat(b_query, self.broll_dir, f"{scene_idx:02d}_{b_idx:02d}")
            is_video = media_path.suffix.lower() in [".webm", ".mp4", ".mkv", ".mov"]

            if is_video:
                fc = (
                    f"[0:v]scale={self.w}:{self.h}:force_original_aspect_ratio=increase,"
                    f"crop={self.w}:{self.h},fps=30[v]"
                )
                cmd = [
                    "ffmpeg", "-y",
                    "-stream_loop", "-1", "-i", str(media_path),
                    "-filter_complex", fc,
                    "-map", "[v]",
                    "-c:v", "libx264", "-preset", "veryfast",
                    "-pix_fmt", "yuv420p",
                    "-t", f"{b_dur:.3f}",
                    "-an",
                    str(beat_clip_path)
                ]
            else:
                d_frames = int(b_dur * 30) + 15
                sw, sh = (int(self.w * 1.25), int(self.h * 1.25))
                motion_mode = b_idx % 4
                if motion_mode == 0:
                    zp = f"zoompan=z='min(zoom+0.0006,1.12)':d={d_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={self.w}x{self.h}:fps=30"
                elif motion_mode == 1:
                    zp = f"zoompan=z='max(1.12-0.0006*on,1.0)':d={d_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={self.w}x{self.h}:fps=30"
                elif motion_mode == 2:
                    zp = f"zoompan=z=1.08:d={d_frames}:x='(iw-iw/zoom)*(on/{d_frames})':y='ih/2-(ih/zoom/2)':s={self.w}x{self.h}:fps=30"
                else:
                    zp = f"zoompan=z=1.08:d={d_frames}:x='(iw-iw/zoom)*(1-on/{d_frames})':y='ih/2-(ih/zoom/2)':s={self.w}x{self.h}:fps=30"

                fade_out_st = max(0.1, b_dur - 0.25)
                fc = (
                    f"[0:v]scale={sw}:{sh}:force_original_aspect_ratio=increase,"
                    f"crop={sw}:{sh},"
                    f"{zp},"
                    f"fade=t=in:st=0:d=0.25,fade=t=out:st={fade_out_st:.2f}:d=0.25[v]"
                )
                cmd = [
                    "ffmpeg", "-y",
                    "-loop", "1", "-i", str(media_path),
                    "-filter_complex", fc,
                    "-map", "[v]",
                    "-c:v", "libx264", "-preset", "veryfast",
                    "-pix_fmt", "yuv420p",
                    "-t", f"{b_dur:.3f}",
                    "-an",
                    str(beat_clip_path)
                ]

            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            beat_clips.append(beat_clip_path)

        # Concatenate beat sub-clips for this scene
        concat_txt = self.shots_dir / f"scene_{scene_idx:02d}_concat.txt"
        with open(concat_txt, "w") as f:
            for bc in beat_clips:
                f.write(f"file '{bc.resolve()}'\n")

        raw_scene_video = self.shots_dir / f"scene_{scene_idx:02d}_raw_video.mp4"
        cmd_cat = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_txt),
            "-c", "copy",
            str(raw_scene_video)
        ]
        subprocess.run(cmd_cat, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Mux uninterrupted continuous voiceover audio onto the dynamic video track
        cmd_mux = [
            "ffmpeg", "-y",
            "-i", str(raw_scene_video),
            "-i", str(audio_file),
            "-map", "0:v",
            "-map", "1:a",
            "-c:v", "copy",
            "-c:a", "aac",
            "-t", f"{duration:.3f}",
            str(out_shot)
        ]
        subprocess.run(cmd_mux, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return out_shot

    def compile_real_video(self, scenes: List[Dict[str, Any]], bg_music: Optional[Path], output_path: Path):
        """Compiles full documentary video from real B-roll shots with ambient audio and no subtitles."""
        shot_paths = []
        total_duration = 0.0

        for idx, scene in enumerate(scenes):
            shot = self.render_shot(scene, idx)
            shot_paths.append(shot)
            total_duration += float(scene.get("duration", 4.0))

        # Write concat list
        concat_txt = self.work_dir / "real_concat.txt"
        with open(concat_txt, "w") as f:
            for sp in shot_paths:
                f.write(f"file '{sp.resolve()}'\n")

        raw_concat = self.work_dir / "real_raw.mp4"
        cmd_cat = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_txt),
            "-c", "copy",
            str(raw_concat)
        ]
        subprocess.run(cmd_cat, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Mix documentary background music if requested
        if bg_music and bg_music.exists():
            fc = (
                "[0:a]volume=1.0[voice];"
                "[1:a]volume=0.10[bg];"
                "[voice][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]"
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
                str(output_path)
            ]
        else:
            cmd_mix = [
                "ffmpeg", "-y",
                "-i", str(raw_concat),
                "-c", "copy",
                "-movflags", "+faststart",
                str(output_path)
            ]

        subprocess.run(cmd_mix, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
