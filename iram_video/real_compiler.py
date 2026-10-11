import math
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

from .b_roll import MediaFetcher
from .audio_synth import synthesize_mood_track
from .ai_video import AIVideoEngine
from .motion_canvas import MotionCanvas, classify_semantic_beat
from .subtitles import KineticSubtitleGenerator

class RealVideoCompiler:
    """
    Compiles realistic documentary-style YouTube videos with AI video models (Veo/Wan/Kling),
    curated verified 4K B-roll photography, and deterministic programmatic motion graphics
    (route maps and animated metric cards).
    Features dynamic audio sidechain ducking and smoothstep Ken Burns easing.
    """

    def __init__(self, work_dir: Path, is_shorts: bool = False, provider: str = "auto", global_topic: str = ""):
        self.work_dir = work_dir
        self.is_shorts = is_shorts
        self.provider = provider
        self.global_topic = global_topic
        self.broll_dir = work_dir / "broll_media"
        self.broll_dir.mkdir(parents=True, exist_ok=True)
        self.shots_dir = work_dir / "real_shots"
        self.shots_dir.mkdir(parents=True, exist_ok=True)
        self.w = 1080 if is_shorts else 1920
        self.h = 1920 if is_shorts else 1080

    def _render_single_shot(self, beat: Dict[str, Any], duration: float, audio_file: Path, out_shot: Path, scene_idx: int) -> Path:
        beat_type = beat.get("beat_type", "real_media")
        query = beat.get("query") or beat.get("phrase") or self.global_topic or "documentary landscape"

        if beat_type == "metric_card":
            tmp_video = self.shots_dir / f"tmp_single_{scene_idx:02d}.mp4"
            MotionCanvas.render_metric_card(beat, tmp_video, duration=duration, is_shorts=self.is_shorts)
            cmd_mux = [
                "ffmpeg", "-y",
                "-i", str(tmp_video),
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
        elif beat_type == "route_map":
            tmp_video = self.shots_dir / f"tmp_single_{scene_idx:02d}.mp4"
            MotionCanvas.render_route_map(beat, tmp_video, duration=duration, is_shorts=self.is_shorts)
            cmd_mux = [
                "ffmpeg", "-y",
                "-i", str(tmp_video),
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

        media_path = AIVideoEngine.fetch_or_generate_beat_media(
            beat, self.broll_dir, f"scene_{scene_idx:02d}", is_shorts=self.is_shorts, provider=self.provider, global_topic=self.global_topic
        )
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
            try:
                from PIL import Image
                Image.MAX_IMAGE_PIXELS = None
                with Image.open(media_path) as im:
                    if im.width > 2560 or im.height > 1440:
                        im.thumbnail((2560, 1440), Image.Resampling.LANCZOS)
                        im.convert("RGB").save(media_path, format="JPEG", quality=92)
            except Exception:
                pass

            d_frames = int(duration * 30) + 30
            sw, sh = (int(self.w * 1.3), int(self.h * 1.3))
            # Smoothstep easing zoompan
            zp = f"zoompan=z='1.0+0.10*(3*pow(on/{d_frames},2)-2*pow(on/{d_frames},3))':d={d_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={self.w}x{self.h}:fps=30"
            fc = (
                f"[0:v]scale={sw}:{sh}:force_original_aspect_ratio=increase,"
                f"crop={sw}:{sh},"
                f"{zp},"
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

        # Extract rapid visual beats (cutting on sentence boundaries with semantic classifier)
        beats = MediaFetcher.extract_scene_beats(scene, duration, global_topic=self.global_topic)

        if len(beats) <= 1:
            beat = beats[0] if beats else {"query": self.global_topic, "duration": duration}
            return self._render_single_shot(beat, duration, audio_file, out_shot, scene_idx)

        # Render each beat sub-clip
        beat_clips = []
        for b_idx, beat in enumerate(beats):
            b_dur = float(beat["duration"])
            beat_clip_path = self.shots_dir / f"beat_{scene_idx:02d}_{b_idx:02d}.mp4"
            beat_type = beat.get("beat_type", "real_media")

            # Route 1: Programmatic Metric Card
            if beat_type == "metric_card":
                MotionCanvas.render_metric_card(
                    beat, beat_clip_path, duration=b_dur, is_shorts=self.is_shorts
                )
                beat_clips.append(beat_clip_path)
                continue

            # Route 2: Programmatic Route Map Blueprint
            if beat_type == "route_map":
                MotionCanvas.render_route_map(
                    beat, beat_clip_path, duration=b_dur, is_shorts=self.is_shorts
                )
                beat_clips.append(beat_clip_path)
                continue

            # Route 3: Real Curated 4K B-Roll / AI Generative Video
            media_path = AIVideoEngine.fetch_or_generate_beat_media(
                beat, self.broll_dir, f"{scene_idx:02d}_{b_idx:02d}", is_shorts=self.is_shorts, provider=self.provider, global_topic=self.global_topic
            )
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
                try:
                    from PIL import Image
                    Image.MAX_IMAGE_PIXELS = None
                    with Image.open(media_path) as im:
                        if im.width > 2560 or im.height > 1440:
                            im.thumbnail((2560, 1440), Image.Resampling.LANCZOS)
                            im.convert("RGB").save(media_path, format="JPEG", quality=92)
                except Exception:
                    pass

                d_frames = int(b_dur * 30) + 15
                sw, sh = (int(self.w * 1.25), int(self.h * 1.25))

                # Non-linear camera easing curves (smoothstep polynomial: 3*t^2 - 2*t^3)
                motion_mode = b_idx % 4
                if motion_mode == 0:
                    zp = f"zoompan=z='1.0+0.10*(3*pow(on/{d_frames},2)-2*pow(on/{d_frames},3))':d={d_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={self.w}x{self.h}:fps=30"
                elif motion_mode == 1:
                    zp = f"zoompan=z='1.10-0.10*(3*pow(on/{d_frames},2)-2*pow(on/{d_frames},3))':d={d_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={self.w}x{self.h}:fps=30"
                elif motion_mode == 2:
                    zp = f"zoompan=z=1.08:d={d_frames}:x='(iw-iw/zoom)*(3*pow(on/{d_frames},2)-2*pow(on/{d_frames},3))':y='ih/2-(ih/zoom/2)':s={self.w}x{self.h}:fps=30"
                else:
                    zp = f"zoompan=z=1.08:d={d_frames}:x='(iw-iw/zoom)*(1-(3*pow(on/{d_frames},2)-2*pow(on/{d_frames},3)))':y='ih/2-(ih/zoom/2)':s={self.w}x{self.h}:fps=30"

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

    def compile_real_video(
        self,
        scenes: List[Dict[str, Any]],
        bg_music: Optional[Path],
        output_path: Path,
        global_topic: str = "",
        burn_subtitles: bool = False,
        language: str = "en"
    ):
        """
        Compiles full documentary video from real B-roll shots and programmatic motion graphics
        with dynamic audio sidechain compression ducking.
        """
        if global_topic:
            self.global_topic = global_topic
        MediaFetcher.reset_session()
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

        # Optional kinetic subtitles filter
        v_filters = []
        if burn_subtitles:
            ass_path = self.work_dir / "real_subtitles.ass"
            KineticSubtitleGenerator.generate_ass(scenes, ass_path, is_shorts=self.is_shorts, language=language)
            if ass_path.exists():
                ass_escaped = str(ass_path).replace("\\", "/").replace(":", "\\:")
                v_filters.append(f"ass={ass_escaped}")

        # Mix documentary background music with Dynamic Audio Sidechain Ducking
        if bg_music and bg_music.exists():
            fc = (
                "[1:a]volume=0.28[bg];"
                "[bg][0:a]sidechaincompress=threshold=0.08:ratio=5:attack=80:release=380[ducked];"
                "[0:a][ducked]amix=inputs=2:duration=first:dropout_transition=2[aout]"
            )
            cmd_mix = [
                "ffmpeg", "-y",
                "-i", str(raw_concat),
                "-i", str(bg_music),
                "-filter_complex", fc,
                "-map", "0:v",
                "-map", "[aout]",
            ]
            if v_filters:
                cmd_mix.extend(["-vf", ",".join(v_filters), "-c:v", "libx264", "-preset", "veryfast"])
            else:
                cmd_mix.extend(["-c:v", "copy"])

            cmd_mix.extend([
                "-c:a", "aac",
                "-b:a", "256k",
                "-movflags", "+faststart",
                str(output_path)
            ])
        else:
            cmd_mix = [
                "ffmpeg", "-y",
                "-i", str(raw_concat)
            ]
            if v_filters:
                cmd_mix.extend(["-vf", ",".join(v_filters), "-c:v", "libx264", "-preset", "veryfast"])
            else:
                cmd_mix.extend(["-c:v", "copy"])

            cmd_mix.extend([
                "-movflags", "+faststart",
                str(output_path)
            ])

        subprocess.run(cmd_mix, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
