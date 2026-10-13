"""
Cinematic Color Grading & Visual Mood System for IRAM Video.
Provides FFmpeg video filter chains for enterprise editorial,
Hollywood cinema, vintage 35mm, high-contrast monochrome, and vibrant marketing palettes.
"""

from typing import Dict, Any, Optional

COLOR_GRADE_PRESETS = {
    "clean": {
        "name": "Editorial Clean",
        "description": "Natural enterprise balance with crisp contrast and faithful saturation.",
        "ffmpeg_filter": "eq=contrast=1.02:brightness=0.0:saturation=1.02"
    },
    "documentary": {
        "name": "Warm Documentary",
        "description": "Natural earth tones, gentle warmth, and balanced documentary highlights.",
        "ffmpeg_filter": "eq=contrast=1.03:brightness=0.01:saturation=1.03,colorbalance=rs=0.03:gs=0.01:bs=-0.02"
    },
    "cinematic": {
        "name": "Hollywood Scope",
        "description": "Subtle teal & orange color grading with cinematic dynamic range.",
        "ffmpeg_filter": "colorbalance=rs=0.06:gs=-0.03:bs=-0.06:rm=-0.03:gm=0.0:bm=0.08:rh=-0.03:gh=0.03:bh=0.12,eq=contrast=1.04:saturation=1.04"
    },
    "vintage": {
        "name": "35mm Analog Film",
        "description": "Nostalgic golden-era film tone with subtle organic texture.",
        "ffmpeg_filter": "eq=contrast=0.98:brightness=0.02:saturation=0.92,colorbalance=rs=0.05:gs=0.02:bs=-0.04,noise=alls=8:allf=t+u"
    },
    "noir": {
        "name": "Dramatic Monochrome",
        "description": "High-contrast black & white with deep obsidian shadows and crisp highlights.",
        "ffmpeg_filter": "hue=s=0,eq=contrast=1.12:brightness=-0.02"
    },
    "vibrant": {
        "name": "Vibrant Promo & Tech",
        "description": "High-impact punchy colors with heightened contrast for marketing and launch showcases.",
        "ffmpeg_filter": "eq=contrast=1.06:brightness=0.01:saturation=1.14"
    },
    "none": {
        "name": "Passthrough",
        "description": "No color alteration.",
        "ffmpeg_filter": "null"
    }
}

def get_color_grade_filter(grade_key: Optional[str]) -> str:
    """Returns the FFmpeg filter string for a given color grade preset."""
    if not grade_key:
        return COLOR_GRADE_PRESETS["clean"]["ffmpeg_filter"]
    key = grade_key.lower().strip().replace("-", "_").replace(" ", "_")
    preset = COLOR_GRADE_PRESETS.get(key, COLOR_GRADE_PRESETS["clean"])
    return preset["ffmpeg_filter"]
