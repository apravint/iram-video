import re
import math
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont

from .renderer import (
    get_fonts,
    get_mixed_width,
    draw_mixed_line,
    wrap_text,
    is_tamil_text,
)

CORRIDOR_PRESETS = {
    "corridor_3": {
        "name_en": "CORRIDOR 3: MADHAVARAM → SIPCOT 2",
        "name_ta": "பாதை 3: மாதவரம் → சிப்காட் 2 (45.8 கி.மீ)",
        "color": (168, 85, 247),  # Purple line
        "stations": [
            ("Madhavaram", "மாதவரம்"),
            ("Ayanavaram", "அயனாவரம்"),
            ("Kilpauk", "கீழ்ப்பாக்கம்"),
            ("Thousand Lights", "ஆயிரம் விளக்கு"),
            ("Adyar Depot", "அடையாறு"),
            ("Thoraipakkam", "துரைப்பாக்கம்"),
            ("SIPCOT 2", "சிப்காட் 2")
        ]
    },
    "corridor_4": {
        "name_en": "CORRIDOR 4: LIGHTHOUSE → POONAMALLEE",
        "name_ta": "பாதை 4: கலங்கரை விளக்கம் → பூந்தமல்லி (26.1 கி.மீ)",
        "color": (255, 138, 0),  # Orange line
        "stations": [
            ("Lighthouse", "கலங்கரை விளக்கம்"),
            ("Nandanam", "நந்தனம்"),
            ("Kodambakkam", "கோடம்பாக்கம்"),
            ("Vadapalani", "வடபழனி"),
            ("Porur", "போரூர்"),
            ("Iyyappanthangal", "ஐயப்பன்தாங்கல்"),
            ("Poonamallee", "பூந்தமல்லி")
        ]
    },
    "corridor_5": {
        "name_en": "CORRIDOR 5: MADHAVARAM → SHOLINGANALLUR",
        "name_ta": "பாதை 5: மாதவரம் → சோழிங்கநல்லூர் (47.0 கி.மீ)",
        "color": (239, 68, 68),  # Red line
        "stations": [
            ("Madhavaram", "மாதவரம்"),
            ("Villivakkam", "வில்லிவாக்கம்"),
            ("Koyambedu", "கோயம்பேடு"),
            ("Alandur", "ஆலந்தூர்"),
            ("Madipakkam", "மடிப்பாக்கம்"),
            ("Medavakkam", "மேடவாக்கம்"),
            ("Sholinganallur", "சோழிங்கநல்லூர்")
        ]
    }
}


def classify_semantic_beat(phrase: str, global_topic: str = "") -> Dict[str, Any]:
    """
    Classifies a spoken phrase or beat into 'metric_card', 'route_map', or 'real_media'.
    Extracts relevant structural metadata for programmatic rendering.
    """
    text = (phrase or "").strip()
    t_low = text.lower()
    top_low = (global_topic or "").lower()

    # 1. Route Map / Corridor Detection
    c3_match = any(k in t_low for k in ["corridor 3", "பாதை 3", "தடம் 3", "madhavaram to sipcot", "மாதவரம் முதல் சிப்காட்", "மாதவரம்"])
    c4_match = any(k in t_low for k in ["corridor 4", "பாதை 4", "தடம் 4", "lighthouse", "poonamallee", "கலங்கரை விளக்கம்", "பூந்தமல்லி"])
    c5_match = any(k in t_low for k in ["corridor 5", "பாதை 5", "தடம் 5", "sholinganallur", "சோழிங்கநல்லூர்"])
    generic_route = any(k in t_low for k in ["route map", "வழித்தடம்", "alignment", "interchange", "இணைக்கும் பாதைகள்", "corridors"])

    if c3_match or c4_match or c5_match or generic_route:
        preset_key = "corridor_3"
        if c4_match:
            preset_key = "corridor_4"
        elif c5_match:
            preset_key = "corridor_5"
        elif "4" in t_low:
            preset_key = "corridor_4"
        elif "5" in t_low:
            preset_key = "corridor_5"

        preset = CORRIDOR_PRESETS[preset_key]
        return {
            "beat_type": "route_map",
            "route_name_en": preset["name_en"],
            "route_name_ta": preset["name_ta"],
            "line_color": preset["color"],
            "stations": preset["stations"],
            "phrase": text
        }

    # 2. Metric Card / Statistical Infographic Detection
    # Look for prominent numbers with units (km, stations, crore, %, etc.)
    num_patterns = [
        r'(\d+[\.,]?\d*)\s*(?:கி\.மீ|km|kilometers?)',
        r'(\d+)\s*(?:நிலையங்கள்|stations?)',
        r'(?:₹|ரூபாய்|rs\.?)\s*(\d+[\.,]?\d*)\s*(?:கோடி|crores?)?',
        r'(\d+[\.,]?\d*)\s*(?:கோடி|crores?|cr)',
        r'(\d+[\.,]?\d*)\s*%',
        r'(\d+)\s*(?:புதிய பாதைகள்|corridors?|lines?)',
        r'(\d+)\s*(?:ரயில்கள்|trains?|coaches?)'
    ]

    for pat in num_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val_str = m.group(1).replace(",", "")
            try:
                num_val = float(val_str)
            except ValueError:
                num_val = 100.0

            # Derive unit and label
            matched_segment = m.group(0)
            if any(u in matched_segment.lower() for u in ["km", "கி.மீ", "kilometer"]):
                unit = "KM / கி.மீ"
                label = "TOTAL NETWORK LENGTH"
                label_ta = "இரண்டாம் கட்ட மொத்த நீளம்"
            elif any(u in matched_segment.lower() for u in ["station", "நிலையம்"]):
                unit = "STATIONS"
                label = "METRO STATIONS"
                label_ta = "மொத்த மெட்ரோ நிலையங்கள்"
            elif any(u in matched_segment.lower() for u in ["crore", "கோடி", "₹", "rs", "ரூபாய்"]):
                unit = "CRORES / கோடி"
                label = "PROJECT BUDGET"
                label_ta = "திட்ட மதிப்பீடு"
            elif "%" in matched_segment:
                unit = "%"
                label = "PROGRESS RATE"
                label_ta = "பணிகள் முன்னேற்றம்"
            elif any(u in matched_segment.lower() for u in ["corridor", "பாதை"]):
                unit = "CORRIDORS"
                label = "EXPANSION LINES"
                label_ta = "புதிய வழித்தடங்கள்"
            else:
                unit = ""
                label = "KEY METRIC"
                label_ta = "முக்கிய விவரம்"

            return {
                "beat_type": "metric_card",
                "metric_number": num_val,
                "metric_unit": unit,
                "metric_label_en": label,
                "metric_label_ta": label_ta,
                "phrase": text
            }

    # 3. Default: Real Media (curated authentic B-roll or AI video)
    return {
        "beat_type": "real_media",
        "phrase": text
    }


class MotionCanvas:
    """
    Programmatic Motion Graphics Engine rendering 30 FPS MP4 video clips directly
    via streaming FFmpeg pipes. Emulates HyperFrames, Claude-Motion, and Remotion
    visual standards with zero external daemons.
    """

    @staticmethod
    def _create_ffmpeg_writer(out_path: Path, width: int, height: int, fps: int = 30) -> subprocess.Popen:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{width}x{height}",
            "-pix_fmt", "rgb24",
            "-r", str(fps),
            "-i", "-",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            str(out_path)
        ]
        return subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @classmethod
    def render_metric_card(
        cls,
        beat: Dict[str, Any],
        out_path: Path,
        duration: float = 4.0,
        is_shorts: bool = False,
        language: str = "ta"
    ) -> Path:
        """
        Renders a glowing glassmorphism metric counter card with cubic ease-out number animation.
        """
        w = 1080 if is_shorts else 1920
        h = 1920 if is_shorts else 1080
        fps = 30
        total_frames = max(30, int(round(duration * fps)))

        target_num = float(beat.get("metric_number", 116.0))
        unit = beat.get("metric_unit", "KM")
        is_tamil = (language.lower() in ["ta", "tamil"]) or is_tamil_text(beat.get("phrase", ""))

        label_en = beat.get("metric_label_en", "KEY STATISTIC")
        label_ta = beat.get("metric_label_ta", "முக்கிய விவரம்")
        headline = label_ta if is_tamil else label_en
        subheadline = label_en if is_tamil else label_ta
        phrase_excerpt = beat.get("phrase", "")[:75]

        # Colors
        c_bg = (10, 14, 24)
        c_card = (16, 24, 40)
        c_accent = (0, 229, 255)
        c_glow = (168, 85, 247)
        c_white = (255, 255, 255)
        c_dim = (140, 165, 200)

        # Card bounds
        if not is_shorts:
            card_x1, card_y1, card_x2, card_y2 = 360, 200, 1560, 880
        else:
            card_x1, card_y1, card_x2, card_y2 = 80, 520, 1000, 1400

        cw = card_x2 - card_x1
        ch = card_y2 - card_y1

        fta_pill, fen_pill = get_fonts(16, bold=True)
        fta_head, fen_head = get_fonts(28, bold=True)
        fta_num, fen_num = get_fonts(84, bold=True)
        fta_unit, fen_unit = get_fonts(38, bold=True)
        fta_sub, fen_sub = get_fonts(20, bold=False)

        proc = cls._create_ffmpeg_writer(out_path, w, h, fps)

        try:
            for frame_idx in range(total_frames):
                p = frame_idx / float(total_frames - 1) if total_frames > 1 else 1.0

                # Cubic Ease-Out curve for number ticker (starts brisk, decelerates into place)
                # Reaches full number by 75% of clip duration so viewer can digest
                p_ticker = min(1.0, p / 0.75)
                eased_ticker = 1.0 - math.pow(1.0 - p_ticker, 3)
                curr_val = target_num * eased_ticker

                img = Image.new("RGB", (w, h), c_bg)
                draw = ImageDraw.Draw(img)

                # 1. Subtle background grid dots
                step = 80 if not is_shorts else 60
                for gx in range(step // 2, w, step):
                    for gy in range(step // 2, h, step):
                        draw.point((gx, gy), fill=(30, 42, 65))

                # 2. Glowing Glassmorphism Card
                draw.rectangle([card_x1, card_y1, card_x2, card_y2], fill=c_card, outline=c_accent, width=2)

                # Outer soft neon shadow lines
                draw.rectangle([card_x1 - 2, card_y1 - 2, card_x2 + 2, card_y2 + 2], outline=(0, 229, 255, 60), width=1)
                draw.rectangle([card_x1 - 4, card_y1 - 4, card_x2 + 4, card_y2 + 4], outline=(0, 229, 255, 30), width=1)

                # 3. Top Status Pill ("● PHASE 2 METRIC" / "● அதிகாரப்பூர்வ விவரம்")
                pill_y = card_y1 + 36
                pill_w = 260
                draw.rectangle([card_x1 + 40, pill_y, card_x1 + 40 + pill_w, pill_y + 36], fill=(24, 34, 56), outline=c_glow, width=1)
                status_txt = "● PHASE 2 METRIC" if not is_tamil else "● இரண்டாம் கட்டம்"
                draw_mixed_line(draw, card_x1 + 54, pill_y + 8, status_txt, c_glow, fta_pill, fen_pill)

                # 4. Metric Headline
                head_y = pill_y + 58
                draw_mixed_line(draw, card_x1 + 40, head_y, headline, c_white, fta_head, fen_head)

                # 5. Animated Number + Unit
                num_y = head_y + 60
                if target_num.is_integer():
                    val_display = f"{int(round(curr_val)):,}"
                else:
                    val_display = f"{curr_val:.1f}"

                nw = get_mixed_width(val_display, fta_num, fen_num, draw)
                draw_mixed_line(draw, card_x1 + 40, num_y, val_display, c_accent, fta_num, fen_num)

                # Unit tag right next to number
                draw_mixed_line(draw, card_x1 + 55 + nw, num_y + 36, unit, c_glow, fta_unit, fen_unit)

                # 6. Animated Glowing Progress Bar Under Number
                bar_y = num_y + 115
                bar_max_w = cw - 80
                bar_w = int(bar_max_w * eased_ticker)
                draw.rectangle([card_x1 + 40, bar_y, card_x1 + 40 + bar_max_w, bar_y + 8], fill=(25, 36, 56))
                if bar_w > 0:
                    draw.rectangle([card_x1 + 40, bar_y, card_x1 + 40 + bar_w, bar_y + 8], fill=c_accent)

                # 7. Subheadline & Narration Context
                sub_y = bar_y + 30
                draw_mixed_line(draw, card_x1 + 40, sub_y, subheadline, c_glow, fta_sub, fen_sub)

                wrapped_ctx = wrap_text(phrase_excerpt, fta_sub, fen_sub, cw - 80, draw)
                ctx_y = sub_y + 36
                for line in wrapped_ctx[:2]:
                    draw_mixed_line(draw, card_x1 + 40, ctx_y, f"• {line}", c_dim, fta_sub, fen_sub)
                    ctx_y += 30

                proc.stdin.write(img.tobytes())

            proc.stdin.close()
            proc.wait()
        except Exception:
            if proc.poll() is None:
                proc.kill()
            raise

        return out_path

    @classmethod
    def render_route_map(
        cls,
        beat: Dict[str, Any],
        out_path: Path,
        duration: float = 4.0,
        is_shorts: bool = False,
        language: str = "ta"
    ) -> Path:
        """
        Renders a dynamic transit blueprint route animation with illuminated station nodes,
        animated line tracing, and radar pulse effects.
        """
        w = 1080 if is_shorts else 1920
        h = 1920 if is_shorts else 1080
        fps = 30
        total_frames = max(30, int(round(duration * fps)))

        route_en = beat.get("route_name_en", "CORRIDOR 3: TRANSIT ROUTE")
        route_ta = beat.get("route_name_ta", "பாதை 3: வழித்தட வரைபடம்")
        is_tamil = (language.lower() in ["ta", "tamil"]) or is_tamil_text(beat.get("phrase", ""))
        title = route_ta if is_tamil else route_en
        line_col = tuple(beat.get("line_color", (168, 85, 247)))

        raw_stations = beat.get("stations", [
            ("Origin", "துவக்கம்"),
            ("Station A", "நிலையம் 1"),
            ("Station B", "நிலையம் 2"),
            ("Station C", "நிலையம் 3"),
            ("Destination", "முடிவு")
        ])

        # Positions along a clean 45-degree isometric metro transit curve
        num_st = len(raw_stations)
        points: List[Tuple[int, int]] = []

        if not is_shorts:
            # Landscape horizontal transit sweep
            x_start, x_end = 220, 1700
            y_base = 560
            for i in range(num_st):
                t_st = i / float(num_st - 1)
                x = int(x_start + (x_end - x_start) * t_st)
                # Metro dogleg curve in center
                y = int(y_base + math.sin(t_st * math.pi) * -90)
                points.append((x, y))
        else:
            # Vertical portrait transit sweep
            y_start, y_end = 420, 1580
            x_base = 380
            for i in range(num_st):
                t_st = i / float(num_st - 1)
                y = int(y_start + (y_end - y_start) * t_st)
                x = int(x_base + math.sin(t_st * math.pi) * 260)
                points.append((x, y))

        fta_badge, fen_badge = get_fonts(16, bold=True)
        fta_title, fen_title = get_fonts(32, bold=True)
        fta_st, fen_st = get_fonts(18, bold=True)
        fta_st_sub, fen_st_sub = get_fonts(14, bold=False)

        proc = cls._create_ffmpeg_writer(out_path, w, h, fps)

        try:
            for frame_idx in range(total_frames):
                p = frame_idx / float(total_frames - 1) if total_frames > 1 else 1.0

                # Tracing progress with ease-in-out
                eased_p = 3.0 * (p ** 2) - 2.0 * (p ** 3)

                img = Image.new("RGB", (w, h), (10, 14, 24))
                draw = ImageDraw.Draw(img)

                # 1. Subtle transit blueprint grid
                grid_step = 80 if not is_shorts else 60
                for gx in range(0, w, grid_step):
                    draw.line([(gx, 0), (gx, h)], fill=(20, 30, 48), width=1)
                for gy in range(0, h, grid_step):
                    draw.line([(0, gy), (w, gy)], fill=(20, 30, 48), width=1)

                # 2. Header Box & Route Identifier
                if not is_shorts:
                    draw.rectangle([120, 70, w - 120, 180], fill=(16, 24, 40), outline=line_col, width=2)
                    draw.rectangle([140, 90, 340, 122], fill=(24, 34, 56), outline=(0, 229, 255), width=1)
                    draw_mixed_line(draw, 155, 96, "● CHENNAI METRO PHASE 2", (0, 229, 255), fta_badge, fen_badge)
                    draw_mixed_line(draw, 140, 132, title, (255, 255, 255), fta_title, fen_title)
                else:
                    draw.rectangle([60, 120, w - 60, 250], fill=(16, 24, 40), outline=line_col, width=2)
                    draw.rectangle([80, 140, 280, 172], fill=(24, 34, 56), outline=(0, 229, 255), width=1)
                    draw_mixed_line(draw, 95, 146, "● METRO CORRIDOR", (0, 229, 255), fta_badge, fen_badge)
                    draw_mixed_line(draw, 80, 185, title[:40], (255, 255, 255), fta_title, fen_title)

                # 3. Draw Inactive Track Line (Dim Grey Blueprint Path)
                for i in range(len(points) - 1):
                    draw.line([points[i], points[i + 1]], fill=(35, 48, 72), width=12)

                # 4. Draw Active Illuminated Track Line (Animated Trace)
                # Compute head coordinate along segments
                total_segs = len(points) - 1
                curr_seg_float = eased_p * total_segs
                curr_seg_idx = min(total_segs - 1, int(curr_seg_float))
                curr_seg_frac = curr_seg_float - curr_seg_idx

                # Fully illuminated completed segments
                for i in range(curr_seg_idx):
                    # Outer soft glow
                    draw.line([points[i], points[i + 1]], fill=tuple(int(c * 0.4) for c in line_col), width=18)
                    # Inner core neon stroke
                    draw.line([points[i], points[i + 1]], fill=line_col, width=10)

                # Partial active segment
                p_from = points[curr_seg_idx]
                p_to = points[curr_seg_idx + 1]
                p_head_x = int(p_from[0] + (p_to[0] - p_from[0]) * curr_seg_frac)
                p_head_y = int(p_from[1] + (p_to[1] - p_from[1]) * curr_seg_frac)

                draw.line([p_from, (p_head_x, p_head_y)], fill=tuple(int(c * 0.4) for c in line_col), width=18)
                draw.line([p_from, (p_head_x, p_head_y)], fill=line_col, width=10)

                # Tracing head spark
                draw.ellipse([(p_head_x - 12, p_head_y - 12), (p_head_x + 12, p_head_y + 12)], fill=(255, 255, 255), outline=line_col, width=3)

                # 5. Station Nodes and Station Labels
                for idx, (st_en, st_ta) in enumerate(raw_stations):
                    sx, sy = points[idx]
                    st_progress_threshold = idx / float(total_segs)
                    is_active = (eased_p >= st_progress_threshold)

                    st_name = st_ta if is_tamil else st_en
                    st_sub = st_en if is_tamil else st_ta

                    if is_active:
                        # Radar pulse ring
                        pulse_r = 18 + int(8 * math.sin(frame_idx * 0.35 + idx))
                        draw.ellipse([(sx - pulse_r, sy - pulse_r), (sx + pulse_r, sy + pulse_r)], outline=(0, 229, 255), width=2)
                        # Solid illuminated station core
                        draw.ellipse([(sx - 10, sy - 10), (sx + 10, sy + 10)], fill=(255, 255, 255), outline=line_col, width=3)
                        text_col = (255, 255, 255)
                        sub_col = (0, 229, 255)
                    else:
                        # Inactive dim dot
                        draw.ellipse([(sx - 7, sy - 7), (sx + 7, sy + 7)], fill=(45, 60, 85), outline=(65, 85, 115), width=2)
                        text_col = (110, 135, 165)
                        sub_col = (75, 95, 125)

                    # Station Label positioning (alternating above and below for landscape)
                    if not is_shorts:
                        is_above = (idx % 2 == 0)
                        lbl_y = sy - 74 if is_above else sy + 30
                        lbl_w = get_mixed_width(st_name, fta_st, fen_st, draw)
                        lbl_x = max(20, min(w - lbl_w - 20, sx - lbl_w // 2))

                        draw_mixed_line(draw, lbl_x, lbl_y, st_name, text_col, fta_st, fen_st)
                        draw_mixed_line(draw, lbl_x, lbl_y + 24, st_sub, sub_col, fta_st_sub, fen_st_sub)
                    else:
                        # Label to the right of node
                        lbl_x = sx + 28
                        lbl_y = sy - 16
                        draw_mixed_line(draw, lbl_x, lbl_y, st_name, text_col, fta_st, fen_st)
                        draw_mixed_line(draw, lbl_x, lbl_y + 24, st_sub, sub_col, fta_st_sub, fen_st_sub)

                proc.stdin.write(img.tobytes())

            proc.stdin.close()
            proc.wait()
        except Exception:
            if proc.poll() is None:
                proc.kill()
            raise

        return out_path
