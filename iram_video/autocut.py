"""
autocut.py — Intelligent scene detection and smart assembly engine.
Detects shot transitions, cuts, and key moments from long-form video or screen recordings,
and rhythmically edits them into target-duration B-roll clips using pure FFmpeg.
Ported and adapted from Automated-Video-Generator architecture.
"""

import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional


def detect_scenes(video_path: Path, sensitivity: float = 0.3) -> List[Dict[str, float]]:
    """
    Detects scene changes and cut points in a video using the FFmpeg scene change filter.
    sensitivity: 0.0 (detect few major cuts) to 1.0 (detect subtle motion cuts).
    Returns list of scene segments: [{'start': float, 'end': float, 'duration': float}].
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Threshold for select='gt(scene,threshold)'
    # Higher sensitivity means lower threshold
    threshold = max(0.05, min(0.95, 1.0 - sensitivity))

    # Probe total video duration
    dur_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "csv=p=0",
        str(video_path)
    ]
    total_duration = 0.0
    try:
        dur_res = subprocess.run(dur_cmd, capture_output=True, text=True, check=True, timeout=10)
        total_duration = float(dur_res.stdout.strip())
    except Exception:
        total_duration = 10.0

    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-vf", f"select='gt(scene,{threshold:.2f})',showinfo",
        "-f", "null",
        "-"
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        stderr = res.stderr
    except Exception:
        stderr = ""

    pts_matches = re.findall(r"pts_time:([\d\.]+)", stderr)
    cut_points = [float(p) for p in pts_matches]

    # Deduplicate and sort
    cut_points = sorted(list(set(cut_points)))
    
    # Ensure starting at 0.0
    if not cut_points or cut_points[0] > 0.5:
        cut_points.insert(0, 0.0)

    scenes: List[Dict[str, float]] = []
    for i in range(len(cut_points)):
        start = cut_points[i]
        end = cut_points[i + 1] if i + 1 < len(cut_points) else total_duration
        dur = max(0.1, round(end - start, 3))
        scenes.append({
            "start": round(start, 3),
            "end": round(end, 3),
            "duration": dur
        })

    return scenes


def smart_assemble(
    video_path: Path,
    target_duration: float,
    out_path: Path,
    min_scene_duration: float = 1.0,
    max_scene_duration: float = 4.5
) -> Path:
    """
    Assembles a coherent, rhythmically paced edit from long raw footage matching target_duration.
    Picks key detected scenes and trims them to fit nicely within min/max bounds.
    """
    video_path = Path(video_path)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not video_path.exists():
        raise FileNotFoundError(f"Input video not found: {video_path}")

    scenes = detect_scenes(video_path)

    # Filter scenes to acceptable durations
    valid_scenes = []
    for s in scenes:
        if s["duration"] >= min_scene_duration:
            # Clamp to max_scene_duration
            actual_dur = min(s["duration"], max_scene_duration)
            valid_scenes.append({
                "start": s["start"],
                "end": s["start"] + actual_dur,
                "duration": actual_dur
            })

    # If no valid scenes detected (e.g., continuous still video), evenly slice
    if not valid_scenes:
        slice_count = max(1, int(target_duration // 3.0))
        slice_dur = target_duration / slice_count
        cur = 0.0
        for _ in range(slice_count):
            valid_scenes.append({
                "start": cur,
                "end": cur + slice_dur,
                "duration": slice_dur
            })
            cur += slice_dur

    # Select scenes to reach target_duration
    selected = []
    accum = 0.0
    for s in valid_scenes:
        if accum + s["duration"] <= target_duration + 0.5:
            selected.append(s)
            accum += s["duration"]
        if accum >= target_duration:
            break

    if not selected:
        selected = [valid_scenes[0]]

    # Generate FFmpeg trim & concat filtergraph
    # [0:v]trim=start=A:end=B,setpts=PTS-STARTPTS[v0]; ... concat=n=N:v=1:a=0[outv]
    filter_parts = []
    v_labels = []
    for i, s in enumerate(selected):
        lbl = f"v{i}"
        filter_parts.append(
            f"[0:v]trim=start={s['start']:.3f}:end={s['end']:.3f},setpts=PTS-STARTPTS[{lbl}]"
        )
        v_labels.append(f"[{lbl}]")

    concat_filter = f"{''.join(v_labels)}concat=n={len(selected)}:v=1:a=0[outv]"
    filter_parts.append(concat_filter)

    full_filter = ";".join(filter_parts)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-filter_complex", full_filter,
        "-map", "[outv]",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "16",
        "-tune", "film",
        "-pix_fmt", "yuv420p",
        "-t", f"{target_duration:.3f}",
        str(out_path)
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=40)
        return out_path
    except Exception:
        # Fallback to direct clip trim
        fallback_cmd = [
            "ffmpeg", "-y",
            "-ss", f"{selected[0]['start']:.3f}",
            "-i", str(video_path),
            "-t", f"{target_duration:.3f}",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "16",
            "-tune", "film",
            "-pix_fmt", "yuv420p",
            str(out_path)
        ]
        subprocess.run(fallback_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return out_path
