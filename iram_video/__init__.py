"""
IRAM Video: Universal Prompt-to-Video Engine
Powered by Google Gemini 3.8 Flash, Edge Neural TTS, PIL 1080p Rendering, and FFMPEG.
"""

from .sfx import SoundEffectsSynthesizer
from .subtitles import (
    KineticSubtitleGenerator,
    syllable_word_timings,
    ffmpeg_drawtext_escape,
    export_srt,
    export_vtt
)
from .voice import VoiceSynthesizer
from .soundscape_mixer import SoundscapeMixer
from .autocut import detect_scenes, smart_assemble

__version__ = "2.1.0"

__all__ = [
    "SoundEffectsSynthesizer",
    "KineticSubtitleGenerator",
    "syllable_word_timings",
    "ffmpeg_drawtext_escape",
    "export_srt",
    "export_vtt",
    "VoiceSynthesizer",
    "SoundscapeMixer",
    "detect_scenes",
    "smart_assemble",
]
