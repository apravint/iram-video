import subprocess
from pathlib import Path
from typing import List, Dict, Any

class VideoCompiler:
    def __init__(self, work_dir: Path):
        self.work_dir = work_dir
        self.clips_dir = work_dir / "clips"
        self.clips_dir.mkdir(parents=True, exist_ok=True)

    def render_clip(self, scene: Dict[str, Any], slide_img: Path) -> Path:
        sid = scene["id"]
        duration = scene["duration"]
        audio_file = Path(scene["audio_file"])
        out_clip = self.clips_dir / f"{sid}.mp4"

        fade_out = max(0, duration - 0.4)
        vf = f"fade=t=in:st=0:d=0.4,fade=t=out:st={fade_out:.2f}:d=0.4"

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-framerate", "30",
            "-i", str(slide_img),
            "-i", str(audio_file),
            "-vf", vf,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-tune", "stillimage",
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
        if bg_music and bg_music.exists():
            fc = (
                "[0:a]volume=1.0[voice];"
                "[1:a]volume=0.12[bg];"
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
