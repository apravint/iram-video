import math
from pathlib import Path
from typing import List, Dict, Any
from .renderer import is_tamil_text

def format_ass_time(seconds: float) -> str:
    """Formats float seconds into ASS time format: H:MM:SS.cs"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs >= 100:
        cs = 99
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

class KineticSubtitleGenerator:
    """Generates high-retention, word-by-word bouncy karaoke subtitles (Alex Hormozi / CapCut / MrBeast style)."""

    @staticmethod
    def generate_ass(
        scenes: List[Dict[str, Any]],
        out_ass_path: Path,
        is_shorts: bool = False,
        language: str = "en"
    ) -> Path:
        res_x = 1080 if is_shorts else 1920
        res_y = 1920 if is_shorts else 1080

        is_tamil = (language.lower() in ["ta", "tamil"])
        font_name = "Noto Sans Tamil" if is_tamil else "JetBrains Mono"
        font_size = 56 if is_shorts else 44
        margin_v = 440 if is_shorts else 180

        # Primary Colors (AABBGGRR in ASS hex)
        # White text: &H00FFFFFF&, Glow Cyan: &H00FFFF00&, Vivid Gold: &H0000D7FF&
        accent_color = "\\c&H0000D7FF&" if is_shorts else "\\c&H00FFFF00&"

        header = f"""[Script Info]
Title: IRAM Kinetic Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: {res_x}
PlayResY: {res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,3,2,60,60,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []
        timeline_cursor = 0.0

        for scene in scenes:
            text = str(scene.get("narration") or scene.get("title") or "").strip()
            duration = float(scene.get("duration", 4.0))
            scene_start = timeline_cursor
            scene_end = scene_start + duration
            timeline_cursor = scene_end

            if not text:
                continue

            word_timings = scene.get("word_timings", [])
            if word_timings and len(word_timings) >= 1:
                # Millisecond-accurate timing directly from Edge-TTS telemetry
                chunk_size = 3 if len(word_timings) >= 6 else (2 if len(word_timings) >= 4 else len(word_timings))
                chunks = []
                for i in range(0, len(word_timings), chunk_size):
                    chunks.append(word_timings[i:i + chunk_size])

                for c_idx, chunk in enumerate(chunks):
                    c_start = scene_start + chunk[0]["start"]
                    c_end = scene_start + chunk[-1]["end"]
                    if c_idx < len(chunks) - 1:
                        next_c_start = scene_start + chunks[c_idx + 1][0]["start"]
                        c_end = min(c_end + 0.15, next_c_start)

                    for w_idx, active_item in enumerate(chunk):
                        w_start = scene_start + active_item["start"]
                        w_end = scene_start + active_item["end"]
                        if w_idx < len(chunk) - 1:
                            w_end = min(w_end + 0.08, scene_start + chunk[w_idx + 1]["start"])
                        else:
                            w_end = max(w_end, c_end)

                        styled_tokens = []
                        for k, item in enumerate(chunk):
                            w_word = item["word"].upper()
                            if k == w_idx:
                                styled_tokens.append(f"{{{accent_color}\\fscx112\\fscy112}}{w_word}{{\\c&H00FFFFFF&\\fscx100\\fscy100}}")
                            else:
                                styled_tokens.append(w_word)

                        line_text = " ".join(styled_tokens)
                        start_str = format_ass_time(w_start)
                        end_str = format_ass_time(w_end)
                        events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{line_text}")
            else:
                words = text.split()
                if not words:
                    continue

                # Split into punchy 2-4 word phrases
                chunk_size = 3 if len(words) >= 6 else (2 if len(words) >= 4 else len(words))
                chunks = []
                for i in range(0, len(words), chunk_size):
                    chunks.append(words[i:i + chunk_size])

                chunk_duration = duration / max(1, len(chunks))

                for c_idx, chunk in enumerate(chunks):
                    c_start = scene_start + (c_idx * chunk_duration)
                    c_end = c_start + chunk_duration
                    word_dur = chunk_duration / len(chunk)

                    # Micro-animate each word in this chunk
                    for w_idx, active_word in enumerate(chunk):
                        w_start = c_start + (w_idx * word_dur)
                        w_end = w_start + word_dur
                        if w_idx == len(chunk) - 1:
                            w_end = c_end

                        styled_tokens = []
                        for k, w in enumerate(chunk):
                            if k == w_idx:
                                # Active word: Highlighted & slightly scaled
                                styled_tokens.append(f"{{{accent_color}\\fscx112\\fscy112}}{w.upper()}{{\\c&H00FFFFFF&\\fscx100\\fscy100}}")
                            else:
                                styled_tokens.append(w.upper())

                        line_text = " ".join(styled_tokens)
                        start_str = format_ass_time(w_start)
                        end_str = format_ass_time(w_end)
                        events.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{line_text}")

        with open(out_ass_path, "w", encoding="utf-8") as f:
            f.write(header)
            f.write("\n".join(events))
            f.write("\n")

        return out_ass_path
