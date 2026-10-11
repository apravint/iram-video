from pathlib import Path
from typing import Dict, Any, List, Tuple
from PIL import Image, ImageDraw, ImageFont

FONT_EN_BOLD = "/home/apravint/.local/share/fonts/JetBrainsMono/JetBrainsMonoNerdFontPropo-Bold.ttf"
FONT_TA_BOLD = "/usr/share/fonts/truetype/noto/NotoSansTamil-Bold.ttf"

def split_runs(text: str) -> List[Tuple[str, bool]]:
    runs = []
    if not text:
        return runs
    current_run = []
    current_is_ta = None
    for char in text:
        is_ta = "\u0b80" <= char <= "\u0bff"
        if current_is_ta is None:
            current_is_ta = is_ta
            current_run.append(char)
        elif is_ta == current_is_ta:
            current_run.append(char)
        else:
            runs.append(("".join(current_run), current_is_ta))
            current_run = [char]
            current_is_ta = is_ta
    if current_run:
        runs.append(("".join(current_run), current_is_ta))
    return runs

def get_fonts(size: int):
    try:
        f_en = ImageFont.truetype(FONT_EN_BOLD, size)
    except Exception:
        f_en = ImageFont.load_default()
    try:
        f_ta = ImageFont.truetype(FONT_TA_BOLD, size)
    except Exception:
        f_ta = f_en
    return f_ta, f_en

def draw_mixed_line(draw: ImageDraw.Draw, x: int, y: int, text: str, fill, font_ta, font_en) -> int:
    cx = x
    for chunk, is_ta in split_runs(text):
        f = font_ta if is_ta else font_en
        draw.text((cx, y), chunk, fill=fill, font=f)
        bbox = draw.textbbox((cx, y), chunk, font=f)
        cx += (bbox[2] - bbox[0])
    return cx

def generate_thumbnail(title: str, bullets: List[str], theme: Dict[str, Any], output_path: Path, is_shorts: bool = False):
    w, h = (1080, 1920) if is_shorts else (1280, 720)
    
    bg_color = tuple(theme.get("bg", [10, 14, 24])) + (255,)
    accent_color = tuple(theme.get("accent", [0, 229, 255])) + (255,)
    sec_color = tuple(theme.get("secondary", [168, 85, 247])) + (255,)

    img = Image.new("RGBA", (w, h), bg_color)
    draw = ImageDraw.Draw(img)

    for x in range(w):
        r = int(accent_color[0] + (sec_color[0] - accent_color[0]) * (x / w))
        g = int(accent_color[1] + (sec_color[1] - accent_color[1]) * (x / w))
        b = int(accent_color[2] + (sec_color[2] - accent_color[2]) * (x / w))
        draw.line([(x, 0), (x, 8 if is_shorts else 6)], fill=(r, g, b, 255), width=8 if is_shorts else 6)

    if is_shorts:
        # Vertical Shorts Thumbnail Layout (1080x1920)
        draw.rectangle((60, 360, w - 60, 1480), fill=(16, 24, 42), outline=accent_color, width=4)
        draw.rectangle((100, 420, 500, 480), fill=(220, 38, 38))
        fta_cat, fen_cat = get_fonts(24)
        draw_mixed_line(draw, 120, 435, "★ YOUTUBE SHORTS", (255, 255, 255), fta_cat, fen_cat)

        words = title.split(" ")
        mid = max(1, len(words) // 2)
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])

        fta_l1, fen_l1 = get_fonts(54)
        fta_l2, fen_l2 = get_fonts(56)
        draw_mixed_line(draw, 100, 530, line1[:28], (255, 255, 255), fta_l1, fen_l1)
        draw_mixed_line(draw, 100, 620, line2[:30], accent_color, fta_l2, fen_l2)

        draw.rectangle((100, 750, w - 100, 830), fill=(24, 36, 60), outline=sec_color, width=2)
        fta_call, fen_call = get_fonts(26)
        draw_mixed_line(draw, 120, 772, "60 SECONDS EXPLAINER", (255, 215, 0), fta_call, fen_call)

        cy = 900
        fta_check, fen_check = get_fonts(24)
        for b in (bullets[:4] or ["Core Concept", "Key Takeaways", "Real Example"]):
            draw_mixed_line(draw, 100, cy, f"⚡ {b[:32]}", (200, 225, 255), fta_check, fen_check)
            cy += 85
    else:
        # Landscape 16:9 Thumbnail Layout (1280x720)
        draw.rectangle((60, 80, 680, 640), fill=(16, 24, 42), outline=accent_color, width=3)
        draw.rectangle((90, 120, 390, 170), fill=(220, 38, 38))
        fta_cat, fen_cat = get_fonts(22)
        draw_mixed_line(draw, 110, 132, "★ FEATURED GUIDE", (255, 255, 255), fta_cat, fen_cat)

        words = title.split(" ")
        mid = max(1, len(words) // 2)
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])

        fta_line1, fen_line1 = get_fonts(46)
        fta_line2, fen_line2 = get_fonts(48)
        draw_mixed_line(draw, 90, 210, line1[:30], (255, 255, 255), fta_line1, fen_line1)
        draw_mixed_line(draw, 90, 280, line2[:32], accent_color, fta_line2, fen_line2)

        draw.rectangle((90, 380, 650, 440), fill=(24, 36, 60), outline=sec_color, width=2)
        fta_subpill, fen_subpill = get_fonts(22)
        draw_mixed_line(draw, 110, 398, "COMPLETE WALKTHROUGH", (255, 215, 0), fta_subpill, fen_subpill)

        draw.rectangle((720, 80, 1220, 640), fill=(14, 20, 35), outline=sec_color, width=2)
        draw.text((750, 120), "WHAT YOU LEARN:", fill=(255, 255, 255), font=fen_cat)

        cy = 190
        fta_check, fen_check = get_fonts(19)
        for b in (bullets[:5] or ["Core Architecture", "Step-by-Step", "Best Practices"]):
            draw_mixed_line(draw, 750, cy, f"⚡ {b[:36]}", (200, 225, 255), fta_check, fen_check)
            cy += 65

    draw.rectangle((0, 0, w - 1, h - 1), outline=accent_color, width=3)
    img.save(output_path)
