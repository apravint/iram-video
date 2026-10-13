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


def detect_code_language(text: str, topic: str = "") -> Tuple[str, str]:
    """Detects programming language and file extension from text context."""
    comb = f"{text} {topic}".lower()
    if any(k in comb for k in ["c++", "cpp", "clang"]):
        return "cpp", "engine.cpp"
    if any(k in comb for k in ["rust", "cargo", "tokio", "actix"]):
        return "rust", "main.rs"
    if any(k in comb for k in ["golang", "goroutine"]) or bool(re.search(r"\b(go|gin)\b", comb)):
        return "go", "server.go"
    if any(k in comb for k in ["python", "fastapi", "django", "pytorch", "pandas", "numpy", "flask"]) or bool(re.search(r"\bpy\b", comb)):
        return "python", "service.py"
    if any(k in comb for k in ["typescript", "react", "nextjs", "vue", "javascript", "node"]) or bool(re.search(r"\b(ts|js)\b", comb)):
        return "typescript", "index.ts"
    if any(k in comb for k in ["sql", "postgres", "mysql", "sqlite"]) or bool(re.search(r"\b(database|query)\b", comb)):
        return "sql", "query.sql"
    if any(k in comb for k in ["bash", "shell", "terminal", "linux"]) or bool(re.search(r"\b(cli|script)\b", comb)):
        return "bash", "deploy.sh"
    if any(k in comb for k in ["docker", "k8s", "kubernetes", "dockerfile"]):
        return "docker", "compose.yml"
    if any(k in comb for k in ["java", "spring", "jvm", "loom", "graalvm"]):
        return "java", "EnterpriseService.java"
    return "software", "architecture.yaml"


def classify_semantic_beat(phrase: str, global_topic: str = "") -> Dict[str, Any]:
    """
    Classifies a spoken phrase or beat into 'listicle_card', 'step_card', 'comparison_card',
    'quote_card', 'code_card', 'metric_card', 'route_map', or 'real_media'.
    Extracts relevant structural metadata for programmatic rendering.
    """
    text = (phrase or "").strip()
    t_low = text.lower()
    top_low = (global_topic or "").lower()

    # Narrative, Mindset, Documentary, and Cinema topics MUST use Real B-Roll Video, not generic UI cards
    is_narrative = any(k in top_low for k in ["fear", "action", "mindset", "motivation", "discipline", "life", "story", "history", "philosophy", "war", "cinema", "documentary", "truth", "habit", "conquer", "bold"])
    if is_narrative:
        return {
            "beat_type": "real_media",
            "phrase": text
        }

    # 1. Top-N Listicle & Countdown Detection (#1, #2, rank, top 5, winner)
    rank_m = re.search(r'(?:#|rank\s*|number\s*|no\.?\s*)(\d+)', t_low)
    if rank_m or any(k in t_low for k in ["winner", "top choice", "#1 winner", "number one"]):
        rank_num = int(rank_m.group(1)) if rank_m else 1
        is_winner = rank_num == 1 or "winner" in t_low or "#1" in t_low
        return {
            "beat_type": "listicle_card",
            "rank": rank_num,
            "badge": "#1 WINNER" if is_winner else f"#{rank_num}",
            "headline": text[:60],
            "phrase": text
        }

    # 2. Tutorial Step & Workflow Detection (Step 1, Step 2, Phase 1, Setup, Verification)
    step_m = re.search(r'(?:step|stage|phase)\s*(\d+)', t_low)
    if step_m or any(k in t_low for k in ["first,", "second,", "step one", "step two", "prerequisite", "how to install"]):
        step_num = int(step_m.group(1)) if step_m else 1
        return {
            "beat_type": "step_card",
            "step": step_num,
            "badge": f"STEP {step_num:02d}",
            "headline": text[:60],
            "phrase": text
        }

    # 3. Head-to-Head Comparison Detection (vs, versus, compared to)
    if any(k in t_low for k in [" vs ", " versus ", " compared to ", " match up "]):
        return {
            "beat_type": "comparison_card",
            "headline": text[:60],
            "phrase": text
        }

    # 4. Route Map / Transit Corridor Detection
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

    # 5. Metric Card / Statistical Infographic Detection
    num_patterns = [
        r'(\d+[\.,]?\d*)\s*(?:கி\.மீ|km|kilometers?)',
        r'(\d+)\s*(?:நிலையங்கள்|stations?)',
        r'(?:₹|ரூபாய்|rs\.?|\$|€)\s*(\d+[\.,]?\d*)\s*(?:கோடி|crores?|billion|million)?',
        r'(\d+[\.,]?\d*)\s*(?:கோடி|crores?|cr|billion|million|x\b)',
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
            elif any(u in matched_segment.lower() for u in ["$", "€", "billion", "million"]):
                unit = "USD / VALUATION"
                label = "MARKET VALUE"
                label_ta = "மதிப்பீடு"
            elif "%" in matched_segment:
                unit = "%"
                label = "GROWTH & PROGRESS"
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

    # 6. Multi-Language Code & Architecture Card Detection
    code_triggers = [
        "python", "rust", "golang", "go code", "typescript", "javascript", "react",
        "sql", "postgres", "database query", "bash", "linux terminal", "docker",
        "kubernetes", "c++", "cpp", "java", "spring boot", "springboot", "api",
        "virtual thread", "project loom", "graalvm", "microservice", "controller",
        "dependency injection", "syntax", "rest api", "backend code", "concurrency"
    ]
    is_code_beat = any(k in t_low for k in code_triggers)
    is_code_topic = top_low and any(k in top_low for k in ["code", "programming", "software", "developer", "api", "python", "rust", "java", "sql"]) and any(k in t_low for k in ["function", "class", "deploy", "server", "memory", "compile", "scale", "query", "endpoint"])

    if is_code_beat or is_code_topic:
        lang, fname = detect_code_language(text, global_topic)
        return {
            "beat_type": "code_card",
            "headline": text[:60],
            "phrase": text,
            "language": lang,
            "filename": fname,
            "topic": lang
        }

    # 7. Default: Real Media (curated authentic stock B-roll or generative AI video)
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
            "-sws_flags", "lanczos+accurate_rnd",
            "-i", "-",
            "-vf", "setsar=1",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "16",
            "-tune", "animation",
            "-pix_fmt", "yuv420p",
            "-colorspace", "bt709",
            "-color_primaries", "bt709",
            "-color_trc", "bt709",
            "-color_range", "tv",
            "-x264-params", "colorprim=bt709:transfer=bt709:colormatrix=bt709",
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

        # Colors: Clean modern editorial aesthetic (deep slate, crisp white, corporate blue)
        c_bg = (15, 23, 42)
        c_card = (30, 41, 59)
        c_accent = (59, 130, 246)
        c_glow = (148, 163, 184)
        c_white = (248, 250, 252)
        c_dim = (148, 163, 184)

        # Card bounds
        if not is_shorts:
            card_x1, card_y1, card_x2, card_y2 = 360, 200, 1560, 880
        else:
            card_x1, card_y1, card_x2, card_y2 = 80, 520, 1000, 1400

        cw = card_x2 - card_x1
        ch = card_y2 - card_y1

        if is_shorts:
            fta_pill, fen_pill = get_fonts(22, bold=True)
            fta_head, fen_head = get_fonts(38, bold=True)
            fta_num, fen_num = get_fonts(110, bold=True)
            fta_unit, fen_unit = get_fonts(48, bold=True)
            fta_sub, fen_sub = get_fonts(28, bold=False)
        else:
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

                # 2. Sleek Modern Card
                draw.rectangle([card_x1, card_y1, card_x2, card_y2], fill=c_card, outline=(51, 65, 85), width=2)

                # 3. Top Status Pill ("● PHASE 2 METRIC" / "● அதிகாரப்பூர்வ விவரம்")
                pill_y = card_y1 + 36
                pill_w = 260
                draw.rectangle([card_x1 + 40, pill_y, card_x1 + 40 + pill_w, pill_y + 36], fill=(15, 23, 42), outline=(51, 65, 85), width=1)
                status_txt = "● PHASE 2 METRIC" if not is_tamil else "● இரண்டாம் கட்டம்"
                draw_mixed_line(draw, card_x1 + 54, pill_y + 8, status_txt, c_accent, fta_pill, fen_pill)

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
            proc.wait()
            raise
        finally:
            if proc.stdin and not proc.stdin.closed:
                try:
                    proc.stdin.close()
                except Exception:
                    pass
            if proc.poll() is None:
                try:
                    proc.kill()
                except Exception:
                    pass
                proc.wait()

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
                    draw.rectangle([140, 90, 340, 122], fill=(24, 34, 56), outline=(59, 130, 246), width=1)
                    draw_mixed_line(draw, 155, 96, "● CHENNAI METRO PHASE 2", (59, 130, 246), fta_badge, fen_badge)
                    draw_mixed_line(draw, 140, 132, title, (255, 255, 255), fta_title, fen_title)
                else:
                    draw.rectangle([60, 120, w - 60, 250], fill=(16, 24, 40), outline=line_col, width=2)
                    draw.rectangle([80, 140, 280, 172], fill=(24, 34, 56), outline=(59, 130, 246), width=1)
                    draw_mixed_line(draw, 95, 146, "● METRO CORRIDOR", (59, 130, 246), fta_badge, fen_badge)
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
                    # Inner core stroke
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
                        draw.ellipse([(sx - pulse_r, sy - pulse_r), (sx + pulse_r, sy + pulse_r)], outline=(59, 130, 246), width=2)
                        # Solid illuminated station core
                        draw.ellipse([(sx - 10, sy - 10), (sx + 10, sy + 10)], fill=(255, 255, 255), outline=line_col, width=3)
                        text_col = (255, 255, 255)
                        sub_col = (148, 163, 184)
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
            proc.wait()
            raise
        finally:
            if proc.stdin and not proc.stdin.closed:
                try:
                    proc.stdin.close()
                except Exception:
                    pass
            if proc.poll() is None:
                try:
                    proc.kill()
                except Exception:
                    pass
                proc.wait()

        return out_path

    @classmethod
    def get_code_snippet_for_language(cls, lang: str, phrase: str = "") -> Tuple[str, List[Tuple[str, Tuple[int, int, int]]], str, str]:
        c_white = (248, 250, 252)
        c_purple = (168, 85, 247)
        c_sky = (56, 189, 248)
        c_green = (34, 197, 94)
        c_amber = (245, 158, 11)
        c_gray = (148, 163, 184)

        if lang == "python":
            lines = [
                ("@app.get(\"/api/v1/stream\")", c_purple),
                ("async def process_stream(query: QueryModel):", c_sky),
                ("    async with AIClient(timeout=30) as client:", c_white),
                ("        result = await client.generate_pipeline(query.prompt)", c_gray),
                ("        metrics = await Telemetry.record(result.tokens)", c_gray),
                ("        return {\"status\": \"ok\", \"data\": result, \"metrics\": metrics}", c_green),
                ("    # Clean graceful completion", c_gray),
            ]
            return "service.py", lines, "● RUNNING: PYTHON 3.12+ • ASYNCIO EVENT LOOP ACTIVE", "python"

        elif lang == "rust":
            lines = [
                ("#[tokio::main]", c_purple),
                ("async fn main() -> Result<(), Box<dyn Error>> {", c_sky),
                ("    let mut client = ClusterClient::connect(\"127.0.0.1:9092\").await?;", c_white),
                ("    let stream = client.subscribe_topics(&[\"telemetry\"]).await?;", c_gray),
                ("    while let Some(msg) = stream.next().await {", c_purple),
                ("        tokio::spawn(async move { process_frame(msg).await });", c_sky),
                ("    }", c_white),
                ("    Ok(())", c_green),
                ("}", c_white),
            ]
            return "main.rs", lines, "● COMPILED: RUSTC 1.80+ • ZERO-COST ABSTRACTIONS ACTIVE", "rust"

        elif lang == "go":
            lines = [
                ("func HandleStream(w http.ResponseWriter, r *http.Request) {", c_sky),
                ("    ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)", c_white),
                ("    defer cancel()", c_purple),
                ("    ch := make(chan Response, 64)", c_white),
                ("    go workerPool.Dispatch(ctx, ch)", c_sky),
                ("    res := <-ch", c_gray),
                ("    w.Header().Set(\"Content-Type\", \"application/json\")", c_amber),
                ("    json.NewEncoder(w).Encode(res)", c_green),
                ("}", c_white),
            ]
            return "server.go", lines, "● RUNNING: GO 1.23+ • GOROUTINES DISPATCHED", "go"

        elif lang in ("typescript", "javascript"):
            lines = [
                ("interface PipelineConfig {", c_purple),
                ("  endpoint: string; maxRetries: number; concurrency: number;", c_white),
                ("}", c_purple),
                ("export async function runPipeline(cfg: PipelineConfig): Promise<Result> {", c_sky),
                ("  const controller = new AbortController();", c_white),
                ("  const res = await fetch(cfg.endpoint, { signal: controller.signal });", c_gray),
                ("  const payload = await res.json();", c_gray),
                ("  return { status: 200, data: payload, timestamp: Date.now() };", c_green),
                ("}", c_white),
            ]
            return "pipeline.ts", lines, "● RUNNING: NODE / BUN • TYPESCRIPT COMPILED", "typescript"

        elif lang == "sql":
            lines = [
                ("WITH active_pipeline_metrics AS (", c_purple),
                ("  SELECT region_id, COUNT(*) AS tx_volume, AVG(latency_ms) AS avg_lat", c_sky),
                ("  FROM telemetry_events", c_white),
                ("  WHERE created_at >= NOW() - INTERVAL '1 hour'", c_gray),
                ("  GROUP BY region_id", c_purple),
                (")", c_purple),
                ("SELECT region_id, tx_volume, avg_lat", c_white),
                ("FROM active_pipeline_metrics ORDER BY tx_volume DESC LIMIT 10;", c_green),
            ]
            return "analytics.sql", lines, "● QUERY EXECUTION: POSTGRESQL 16 • INDEX SCAN ACCELERATED", "sql"

        elif lang == "bash":
            lines = [
                ("#!/usr/bin/env bash", c_gray),
                ("set -euo pipefail", c_purple),
                ("echo \"[1/3] Validating cluster configuration...\"", c_sky),
                ("docker compose -f docker-compose.prod.yml up -d --build", c_white),
                ("kubectl rollout status deployment/core-engine --timeout=60s", c_amber),
                ("echo \"[✓] Production deployment complete with zero downtime.\"", c_green),
            ]
            return "deploy.sh", lines, "● SHELL ENVIRONMENT: BASH 5.2 • PIPELINE EXECUTED", "bash"

        elif lang == "docker":
            lines = [
                ("services:", c_purple),
                ("  api-gateway:", c_white),
                ("    image: enterprise/gateway:latest", c_sky),
                ("    deploy: { replicas: 8, restart_policy: { condition: on-failure } }", c_gray),
                ("  core-engine:", c_white),
                ("    image: enterprise/engine:v3", c_sky),
                ("    environment: [\"PRODUCTION=true\", \"WORKERS=16\"]", c_amber),
                ("    healthcheck: { test: [\"CMD\", \"curl\", \"-f\", \"/health\"], interval: 10s }", c_green),
            ]
            return "docker-compose.yml", lines, "● CONTAINER ENGINE: DOCKER / K8S • HEALTHY", "docker"

        elif lang == "cpp":
            lines = [
                ("#include <memory>", c_purple),
                ("template<typename T>", c_purple),
                ("class LockFreeRingBuffer {", c_sky),
                ("    std::atomic<size_t> head_{0}, tail_{0};", c_white),
                ("public:", c_purple),
                ("    bool push(const T& item) noexcept {", c_sky),
                ("        // Zero-copy high-throughput lock-free enqueue", c_gray),
                ("        return true;", c_green),
                ("    }", c_white),
                ("};", c_white),
            ]
            return "ring_buffer.hpp", lines, "● COMPILED: CLANG 18 -O3 • LOCK-FREE CONCURRENCY", "cpp"

        else: # java default
            lines = [
                ("@SpringBootApplication", c_purple),
                ("public class EnterpriseService {", c_white),
                ("    @Bean", c_purple),
                ("    public TomcatProtocolHandlerCustomizer<?> protocol() {", c_sky),
                ("        return p -> p.setExecutor(Executors.newVirtualThreadPerTaskExecutor());", c_gray),
                ("    }", c_white),
                ("    @GetMapping(\"/api/v1/scale\")", c_purple),
                ("    public ResponseEntity<Metrics> getMetrics() {", c_sky),
                ("        return ResponseEntity.ok(Metrics.virtualThreadScale());", c_green),
                ("    }", c_white),
                ("}", c_white),
            ]
            return "EnterpriseService.java", lines, "● RUNNING: JVM 21+ • VIRTUAL THREADS ACTIVE", "java"

    @classmethod
    def render_code_card(
        cls,
        beat: Dict[str, Any],
        out_path: Path,
        duration: float = 4.0,
        is_shorts: bool = False,
    ) -> Path:
        """
        Renders a broadcast-quality animated code editor / architecture card with syntax highlighting
        and smooth progressive typing/highlight animation across Python, Rust, Go, TS, SQL, Bash, and Java.
        """
        w = 1080 if is_shorts else 1920
        h = 1920 if is_shorts else 1080
        fps = 30
        total_frames = max(30, int(round(duration * fps)))

        c_bg = (15, 23, 42)
        c_grid = (24, 34, 53)
        c_white = (248, 250, 252)
        c_blue = (59, 130, 246)
        c_sky = (56, 189, 248)
        c_purple = (168, 85, 247)
        c_green = (34, 197, 94)
        c_gray = (148, 163, 184)
        c_dim = (71, 85, 105)

        card_x1, card_y1 = (80, 480) if is_shorts else (240, 160)
        card_x2, card_y2 = (1000, 1440) if is_shorts else (1680, 920)

        fta_head, fen_head = get_fonts(26 if is_shorts else 32, bold=True)
        fta_code, fen_code = get_fonts(18 if is_shorts else 22, bold=False)
        fta_sm, fen_sm = get_fonts(16 if is_shorts else 18, bold=False)

        lang_req = beat.get("language") or beat.get("topic") or "software"
        phrase = beat.get("phrase", "Software Architecture")

        win_title, code_lines, status_txt, _ = cls.get_code_snippet_for_language(lang_req, phrase)
        if beat.get("filename"):
            win_title = beat["filename"]

        proc = cls._create_ffmpeg_writer(out_path, w, h, fps)

        try:
            for frame_idx in range(total_frames):
                p = frame_idx / float(total_frames - 1) if total_frames > 1 else 1.0
                active_lines_count = max(1, min(len(code_lines), int(p * (len(code_lines) + 2))))

                img = Image.new("RGB", (w, h), c_bg)
                draw = ImageDraw.Draw(img)

                # Background grid
                grid_step = 60 if is_shorts else 80
                for gx in range(0, w, grid_step):
                    draw.line([(gx, 0), (gx, h)], fill=c_grid, width=1)
                for gy in range(0, h, grid_step):
                    draw.line([(0, gy), (w, gy)], fill=c_grid, width=1)

                # Top brand line
                draw.rectangle([(0, 0), (w, 6)], fill=c_blue)

                # Headline
                hl_y = 120 if is_shorts else 80
                hl_text = (phrase[:55] + "...") if len(phrase) > 55 else phrase
                draw_mixed_line(draw, card_x1, hl_y, hl_text, c_white, fta_head, fen_head)

                # Card background
                draw.rounded_rectangle(
                    [(card_x1, card_y1), (card_x2, card_y2)],
                    radius=12,
                    fill=(20, 29, 44),
                    outline=(51, 65, 85),
                    width=2
                )

                # Window dots
                draw.ellipse([(card_x1 + 24, card_y1 + 18), (card_x1 + 36, card_y1 + 30)], fill=(100, 116, 139))
                draw.ellipse([(card_x1 + 44, card_y1 + 18), (card_x1 + 56, card_y1 + 30)], fill=(148, 163, 184))
                draw.ellipse([(card_x1 + 64, card_y1 + 18), (card_x1 + 76, card_y1 + 30)], fill=(203, 213, 225))
                draw_mixed_line(draw, card_x1 + 90, card_y1 + 14, win_title, c_gray, fta_sm, fen_sm)
                draw.line([(card_x1, card_y1 + 44), (card_x2, card_y1 + 44)], fill=(30, 41, 59), width=1)

                # Code content
                cy = card_y1 + 65
                line_h = 32 if is_shorts else 38
                for idx, (txt, col) in enumerate(code_lines[:active_lines_count]):
                    if cy + line_h > card_y2 - 35:
                        break
                    draw_mixed_line(draw, card_x1 + 28, cy, f"{idx+1:2d}", c_dim, fta_code, fen_code)
                    draw_mixed_line(draw, card_x1 + 75, cy, txt, col, fta_code, fen_code)
                    cy += line_h

                # Blinking cursor on active line
                if (frame_idx // 8) % 2 == 0 and cy <= card_y2 - 25:
                    cursor_x = card_x1 + 75
                    draw.rectangle([(cursor_x, cy - 2), (cursor_x + 10, cy + 20)], fill=c_sky)

                # Status pill at bottom
                draw_mixed_line(draw, card_x1 + 28, card_y2 - 36, status_txt, c_green, fta_sm, fen_sm)

                proc.stdin.write(img.tobytes())

            proc.stdin.close()
            proc.wait()
        except Exception:
            if proc.poll() is None:
                proc.kill()
            proc.wait()
            raise
        finally:
            if proc.stdin and not proc.stdin.closed:
                try:
                    proc.stdin.close()
                except Exception:
                    pass
            if proc.poll() is None:
                try:
                    proc.kill()
                except Exception:
                    pass
                proc.wait()

        return out_path

    @classmethod
    def render_listicle_card(
        cls,
        beat: Dict[str, Any],
        out_path: Path,
        duration: float = 4.0,
        is_shorts: bool = False
    ) -> Path:
        """
        Renders a dynamic countdown listicle card with glowing rank badge (#1 WINNER, #2, etc.),
        headline, progress bar, and key takeaways.
        """
        w = 1080 if is_shorts else 1920
        h = 1920 if is_shorts else 1080
        fps = 30
        total_frames = max(30, int(round(duration * fps)))

        c_bg = (15, 23, 42)
        c_card = (30, 41, 59)
        c_accent = (59, 130, 246)
        c_gold = (245, 158, 11)
        c_white = (248, 250, 252)
        c_muted = (148, 163, 184)

        card_x1, card_y1 = (80, 500) if is_shorts else (320, 200)
        card_x2, card_y2 = (1000, 1420) if is_shorts else (1600, 880)

        badge_text = beat.get("badge", "#1 WINNER")
        phrase = beat.get("phrase", "Top Contender")
        rank = beat.get("rank", 1)

        fta_badge, fen_badge = get_fonts(28 if is_shorts else 36, bold=True)
        fta_head, fen_head = get_fonts(28 if is_shorts else 38, bold=True)
        fta_sub, fen_sub = get_fonts(20 if is_shorts else 24, bold=False)

        proc = cls._create_ffmpeg_writer(out_path, w, h, fps)
        try:
            for frame_idx in range(total_frames):
                p = frame_idx / float(total_frames - 1) if total_frames > 1 else 1.0
                eased = 1.0 - math.pow(1.0 - p, 3)

                img = Image.new("RGB", (w, h), c_bg)
                draw = ImageDraw.Draw(img)

                # Background dots
                step = 60 if is_shorts else 80
                for gx in range(step // 2, w, step):
                    for gy in range(step // 2, h, step):
                        draw.point((gx, gy), fill=(30, 42, 65))

                # Card box
                draw.rounded_rectangle([(card_x1, card_y1), (card_x2, card_y2)], radius=14, fill=c_card, outline=(51, 65, 85), width=2)

                # Top Rank Pill
                pill_col = c_gold if (rank == 1 or "winner" in badge_text.lower()) else c_accent
                draw.rounded_rectangle([(card_x1 + 40, card_y1 + 40), (card_x1 + 320, card_y1 + 95)], radius=8, fill=(15, 23, 42), outline=pill_col, width=2)
                draw_mixed_line(draw, card_x1 + 60, card_y1 + 48, badge_text, pill_col, fta_badge, fen_badge)

                # Main Headline
                hy = card_y1 + 130
                wrapped_hl = wrap_text(phrase, fta_head, fen_head, (card_x2 - card_x1 - 80), draw)
                for line in wrapped_hl[:3]:
                    draw_mixed_line(draw, card_x1 + 40, hy, line, c_white, fta_head, fen_head)
                    hy += 46

                # Animated Growth Bar
                by = hy + 30
                max_w = card_x2 - card_x1 - 80
                draw.rectangle([(card_x1 + 40, by), (card_x1 + 40 + max_w, by + 10)], fill=(20, 30, 48))
                draw.rectangle([(card_x1 + 40, by), (card_x1 + 40 + int(max_w * eased), by + 10)], fill=pill_col)

                # Evaluation criteria
                tag_y = by + 30
                draw_mixed_line(draw, card_x1 + 40, tag_y, "★ VERIFIED HIGH PERFORMANCE & ARCHITECTURAL IMPACT", c_muted, fta_sub, fen_sub)

                proc.stdin.write(img.tobytes())

            proc.stdin.close()
            proc.wait()
        except Exception:
            if proc.poll() is None:
                proc.kill()
            proc.wait()
            raise
        finally:
            if proc.stdin and not proc.stdin.closed:
                try:
                    proc.stdin.close()
                except Exception:
                    pass
            if proc.poll() is None:
                try:
                    proc.kill()
                except Exception:
                    pass
                proc.wait()

        return out_path

    @classmethod
    def render_step_card(
        cls,
        beat: Dict[str, Any],
        out_path: Path,
        duration: float = 4.0,
        is_shorts: bool = False
    ) -> Path:
        """
        Renders an instructional tutorial step card with step counter badge and actionable instructions.
        """
        w = 1080 if is_shorts else 1920
        h = 1920 if is_shorts else 1080
        fps = 30
        total_frames = max(30, int(round(duration * fps)))

        c_bg = (15, 23, 42)
        c_card = (24, 34, 53)
        c_blue = (59, 130, 246)
        c_green = (34, 197, 94)
        c_white = (248, 250, 252)
        c_muted = (148, 163, 184)

        card_x1, card_y1 = (80, 500) if is_shorts else (320, 200)
        card_x2, card_y2 = (1000, 1420) if is_shorts else (1600, 880)

        badge_text = beat.get("badge", "STEP 01")
        phrase = beat.get("phrase", "Step Action")

        fta_b, fen_b = get_fonts(24 if is_shorts else 30, bold=True)
        fta_h, fen_h = get_fonts(28 if is_shorts else 36, bold=True)
        fta_p, fen_p = get_fonts(20 if is_shorts else 24, bold=False)

        proc = cls._create_ffmpeg_writer(out_path, w, h, fps)
        try:
            for frame_idx in range(total_frames):
                p = frame_idx / float(total_frames - 1) if total_frames > 1 else 1.0

                img = Image.new("RGB", (w, h), c_bg)
                draw = ImageDraw.Draw(img)

                # Grid
                grid_step = 60 if is_shorts else 80
                for gx in range(0, w, grid_step):
                    draw.line([(gx, 0), (gx, h)], fill=(22, 32, 50), width=1)
                for gy in range(0, h, grid_step):
                    draw.line([(0, gy), (w, gy)], fill=(22, 32, 50), width=1)

                draw.rounded_rectangle([(card_x1, card_y1), (card_x2, card_y2)], radius=12, fill=c_card, outline=(51, 65, 85), width=2)

                # Step Pill
                draw.rounded_rectangle([(card_x1 + 40, card_y1 + 40), (card_x1 + 260, card_y1 + 95)], radius=6, fill=(15, 23, 42), outline=c_blue, width=1)
                draw_mixed_line(draw, card_x1 + 60, card_y1 + 52, f"● {badge_text}", c_blue, fta_b, fen_b)

                # Step instruction headline
                hy = card_y1 + 130
                wrapped_hl = wrap_text(phrase, fta_h, fen_h, (card_x2 - card_x1 - 80), draw)
                for line in wrapped_hl[:3]:
                    draw_mixed_line(draw, card_x1 + 40, hy, line, c_white, fta_h, fen_h)
                    hy += 45

                # Terminal action callout
                callout_y = hy + 30
                draw.rectangle([(card_x1 + 40, callout_y), (card_x2 - 40, callout_y + 90)], fill=(15, 23, 42), outline=(51, 65, 85), width=1)
                draw_mixed_line(draw, card_x1 + 65, callout_y + 20, "$ execute --verify --production", (56, 189, 248), fta_p, fen_p)
                draw_mixed_line(draw, card_x1 + 65, callout_y + 54, "[✓] Process initialized successfully", c_green, fta_p, fen_p)

                # Bottom status
                draw_mixed_line(draw, card_x1 + 40, card_y2 - 50, "● WORKFLOW STAGE ACTIVE • VERIFIED STEPS", c_muted, fta_p, fen_p)

                proc.stdin.write(img.tobytes())

            proc.stdin.close()
            proc.wait()
        except Exception:
            if proc.poll() is None:
                proc.kill()
            proc.wait()
            raise
        finally:
            if proc.stdin and not proc.stdin.closed:
                try:
                    proc.stdin.close()
                except Exception:
                    pass
            if proc.poll() is None:
                try:
                    proc.kill()
                except Exception:
                    pass
                proc.wait()

        return out_path

    @classmethod
    def render_comparison_card(
        cls,
        beat: Dict[str, Any],
        out_path: Path,
        duration: float = 4.0,
        is_shorts: bool = False
    ) -> Path:
        """
        Renders a head-to-head comparison matchup card contrasting two options side-by-side.
        """
        w = 1080 if is_shorts else 1920
        h = 1920 if is_shorts else 1080
        fps = 30
        total_frames = max(30, int(round(duration * fps)))

        c_bg = (15, 23, 42)
        c_white = (248, 250, 252)
        c_blue = (59, 130, 246)
        c_amber = (245, 158, 11)
        c_green = (34, 197, 94)

        phrase = beat.get("phrase", "Contender A vs Contender B")
        tokens = [t.strip() for t in re.split(r'\b(?:vs|versus)\b', phrase, flags=re.IGNORECASE) if t.strip()]
        side_a = tokens[0][:40] if len(tokens) >= 1 else "Traditional"
        side_b = tokens[1][:40] if len(tokens) >= 2 else "Modernized"

        fta_head, fen_head = get_fonts(26 if is_shorts else 32, bold=True)
        fta_col, fen_col = get_fonts(22 if is_shorts else 28, bold=True)
        fta_txt, fen_txt = get_fonts(18 if is_shorts else 20, bold=False)

        proc = cls._create_ffmpeg_writer(out_path, w, h, fps)
        try:
            for frame_idx in range(total_frames):
                img = Image.new("RGB", (w, h), c_bg)
                draw = ImageDraw.Draw(img)

                # Header
                draw_mixed_line(draw, 100 if not is_shorts else 60, 80 if not is_shorts else 140, "HEAD-TO-HEAD COMPARISON", c_blue, fta_head, fen_head)

                if not is_shorts:
                    # Landscape Dual Columns
                    col_y, col_h = 180, 720
                    # Left column
                    draw.rounded_rectangle([(100, col_y), (920, col_y + col_h)], radius=12, fill=(24, 34, 53), outline=(51, 65, 85), width=2)
                    draw_mixed_line(draw, 140, col_y + 40, side_a, c_white, fta_col, fen_col)
                    draw.line([(140, col_y + 90), (880, col_y + 90)], fill=(51, 65, 85), width=1)
                    draw_mixed_line(draw, 140, col_y + 130, "• Legacy Architecture & Higher Overhead", (148, 163, 184), fta_txt, fen_txt)
                    draw_mixed_line(draw, 140, col_y + 180, "• Complex Manual Scaling Requirements", (148, 163, 184), fta_txt, fen_txt)
                    draw_mixed_line(draw, 140, col_y + 230, "• Traditional Thread Pool Allocation", (148, 163, 184), fta_txt, fen_txt)

                    # Right column
                    draw.rounded_rectangle([(1000, col_y), (1820, col_y + col_h)], radius=12, fill=(24, 34, 53), outline=c_blue, width=2)
                    draw_mixed_line(draw, 1040, col_y + 40, side_b, c_white, fta_col, fen_col)
                    draw.line([(1040, col_y + 90), (1780, col_y + 90)], fill=c_blue, width=1)
                    draw_mixed_line(draw, 1040, col_y + 130, "✓ Ultra-Low Latency & Memory Footprint", c_green, fta_txt, fen_txt)
                    draw_mixed_line(draw, 1040, col_y + 180, "✓ Automated Elastic Concurrency Scaling", c_green, fta_txt, fen_txt)
                    draw_mixed_line(draw, 1040, col_y + 230, "✓ Modern Zero-Copy Telemetry Out of Box", c_green, fta_txt, fen_txt)
                else:
                    # Vertical Stacked Columns
                    card_w = 920
                    draw.rounded_rectangle([(80, 260), (80 + card_w, 780)], radius=10, fill=(24, 34, 53), outline=(51, 65, 85), width=2)
                    draw_mixed_line(draw, 110, 290, side_a, c_white, fta_col, fen_col)
                    draw_mixed_line(draw, 110, 360, "• Traditional System Setup", (148, 163, 184), fta_txt, fen_txt)
                    draw_mixed_line(draw, 110, 420, "• Standard Resource Scaling", (148, 163, 184), fta_txt, fen_txt)

                    draw.rounded_rectangle([(80, 840), (80 + card_w, 1360)], radius=10, fill=(24, 34, 53), outline=c_blue, width=2)
                    draw_mixed_line(draw, 110, 870, side_b, c_white, fta_col, fen_col)
                    draw_mixed_line(draw, 110, 940, "✓ Optimized Next-Gen Workflow", c_green, fta_txt, fen_txt)
                    draw_mixed_line(draw, 110, 1000, "✓ Cloud-Native High Concurrency", c_green, fta_txt, fen_txt)

                proc.stdin.write(img.tobytes())

            proc.stdin.close()
            proc.wait()
        except Exception:
            if proc.poll() is None:
                proc.kill()
            proc.wait()
            raise
        finally:
            if proc.stdin and not proc.stdin.closed:
                try:
                    proc.stdin.close()
                except Exception:
                    pass
            if proc.poll() is None:
                try:
                    proc.kill()
                except Exception:
                    pass
                proc.wait()

        return out_path

