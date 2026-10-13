"""
Cinematic Video Transition Engine for IRAM Video.
Provides FFmpeg xfade (crossfade, wipe, slide, circlecrop, smooth)
and acrossfade audio blending with seamless fallback to fast concat.
"""

import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any

VALID_TRANSITIONS = {
    "fade": "fade",
    "dissolve": "fade",
    "wipeleft": "wipeleft",
    "wiperight": "wiperight",
    "slideleft": "slideleft",
    "slideright": "slideright",
    "smoothleft": "smoothleft",
    "circlecrop": "circlecrop",
    "rectcrop": "rectcrop",
    "fadeblack": "fadeblack",
    "fadewhite": "fadewhite",
    "radial": "radial",
    "zoomin": "zoomin",
    "cut": "none",
    "none": "none"
}

class TransitionEngine:
    """Orchestrates seamless multi-clip video and audio transitions."""

    @staticmethod
    def get_clip_duration(clip_path: Path) -> float:
        """Probes the exact duration of a video clip via ffprobe."""
        if not clip_path.exists():
            return 0.0
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(clip_path)
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return max(0.1, float(res.stdout.strip()))
        except Exception:
            return 3.0

    @classmethod
    def join_clips_with_transitions(
        cls,
        clip_paths: List[Path],
        output_path: Path,
        transition: str = "fade",
        trans_duration: float = 0.5,
        target_fps: int = 30,
        work_dir: Optional[Path] = None
    ) -> Path:
        """
        Stitches sequential video clips using FFmpeg xfade video transitions
        and acrossfade audio crossfades. If xfade fails, falls back cleanly to concat.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if not clip_paths:
            raise ValueError("No video clips provided to transition engine.")

        if len(clip_paths) == 1:
            cmd = ["ffmpeg", "-y", "-i", str(clip_paths[0]), "-c", "copy", str(output_path)]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return output_path

        t_name = VALID_TRANSITIONS.get(transition.lower().strip(), "fade")
        if t_name == "none":
            return cls._fallback_concat(clip_paths, output_path, work_dir)

        # Probe durations of all clips
        durations = [cls.get_clip_duration(p) for p in clip_paths]

        # Guard: Each clip must be longer than the transition duration
        min_clip_dur = min(durations)
        if min_clip_dur <= trans_duration + 0.3:
            # Scaled down transition duration if clips are short
            trans_duration = max(0.2, min_clip_dur - 0.4)
            if trans_duration < 0.2:
                return cls._fallback_concat(clip_paths, output_path, work_dir)

        # Build FFmpeg filter_complex for N clips
        # [0:v][1:v]xfade=transition=fade:duration=D:offset=OFFSET[v1]; [v1][2:v]xfade...
        try:
            inputs = []
            for p in clip_paths:
                inputs.extend(["-i", str(p)])

            v_filters = []
            a_filters = []

            curr_offset = durations[0] - trans_duration
            prev_v = "0:v"
            prev_a = "0:a"

            for i in range(1, len(clip_paths)):
                out_v = f"v_xf_{i}"
                out_a = f"a_xf_{i}"
                is_last = (i == len(clip_paths) - 1)

                tag_v = f"[{out_v}]" if not is_last else "[v_master]"
                tag_a = f"[{out_a}]" if not is_last else "[a_master]"

                v_filters.append(
                    f"[{prev_v}][{i}:v]xfade=transition={t_name}:duration={trans_duration:.2f}:offset={curr_offset:.2f}{tag_v}"
                )
                a_filters.append(
                    f"[{prev_a}][{i}:a]acrossfade=d={trans_duration:.2f}:c1=tri:c2=tri{tag_a}"
                )

                prev_v = out_v
                prev_a = out_a
                curr_offset = curr_offset + durations[i] - trans_duration

            full_filter = ";".join(v_filters + a_filters)

            cmd = [
                "ffmpeg", "-y",
                *inputs,
                "-filter_complex", full_filter,
                "-map", "[v_master]",
                "-map", "[a_master]",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "18",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                str(output_path)
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return output_path
        except Exception:
            # Automatic graceful fallback to safe concat
            return cls._fallback_concat(clip_paths, output_path, work_dir)

    @classmethod
    def _fallback_concat(cls, clip_paths: List[Path], output_path: Path, work_dir: Optional[Path]) -> Path:
        """Safe fallback concatenation via FFmpeg concat demuxer."""
        td = work_dir or output_path.parent
        concat_txt = td / "transition_fallback_concat.txt"
        with open(concat_txt, "w") as f:
            for cp in clip_paths:
                f.write(f"file '{cp.resolve()}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_txt),
            "-c", "copy",
            str(output_path)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_path
