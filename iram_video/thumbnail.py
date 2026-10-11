from pathlib import Path
from typing import Dict, Any, List
from PIL import Image, ImageDraw, ImageFont

FONT_EN_BOLD = "/home/apravint/.local/share/fonts/JetBrainsMono/JetBrainsMonoNerdFontPropo-Bold.ttf"
FONT_TA_BOLD = "/usr/share/fonts/truetype/noto/NotoSansTamil-Bold.ttf"

def is_tamil_text(text: str) -> bool:
    return any("\u0b80" <= c <= "\u0bff" for c in str(text))

def get_font_for_text(text: str, size: int):
    p = FONT_TA_BOLD if is_tamil_text(text) else FONT_EN_BOLD
    try:
        return ImageFont.truetype(p, size)
    except Exception:
        return ImageFont.load_default()

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
        # Center box (y=400 to 1450)
        draw.rectangle((60, 360, w - 60, 1480), fill=(16, 24, 42), outline=accent_color, width=4)
        
        # Category Pill
        draw.rectangle((100, 420, 480, 480), fill=(220, 38, 38))
        f_cat = get_font_for_text("★ YOUTUBE SHORTS", 24)
        draw.text((120, 435), "★ YOUTUBE SHORTS", fill=(255, 255, 255), font=f_cat)

        words = title.split(" ")
        mid = max(1, len(words) // 2)
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])

        f_l1 = get_font_for_text(line1, 56)
        f_l2 = get_font_for_text(line2, 58)
        draw.text((100, 530), line1[:28], fill=(255, 255, 255), font=f_l1)
        draw.text((100, 620), line2[:30], fill=accent_color, font=f_l2)

        draw.rectangle((100, 750, w - 100, 830), fill=(24, 36, 60), outline=sec_color, width=2)
        f_callout = get_font_for_text("60 SECONDS EXPLAINER", 26)
        draw.text((120, 772), "60 SECONDS EXPLAINER", fill=(255, 215, 0), font=f_callout)

        # Bullets
        cy = 900
        for b in (bullets[:4] or ["Core Concept", "Key Takeaways", "Real Example"]):
            f_check = get_font_for_text(b, 24)
            draw.text((100, cy), f"⚡ {b[:32]}", fill=(200, 225, 255), font=f_check)
            cy += 85
    else:
        # Landscape 16:9 Thumbnail Layout (1280x720)
        draw.rectangle((60, 80, 680, 640), fill=(16, 24, 42), outline=accent_color, width=3)
        draw.rectangle((90, 120, 390, 170), fill=(220, 38, 38))
        f_cat = get_font_for_text("★ FEATURED GUIDE", 22)
        draw.text((110, 132), "★ FEATURED GUIDE", fill=(255, 255, 255), font=f_cat)

        words = title.split(" ")
        mid = max(1, len(words) // 2)
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])

        f_line1 = get_font_for_text(line1, 46)
        f_line2 = get_font_for_text(line2, 48)
        draw.text((90, 210), line1[:30], fill=(255, 255, 255), font=f_line1)
        draw.text((90, 280), line2[:32], fill=accent_color, font=f_line2)

        draw.rectangle((90, 380, 650, 440), fill=(24, 36, 60), outline=sec_color, width=2)
        f_subpill = get_font_for_text("COMPLETE WALKTHROUGH", 22)
        draw.text((110, 398), "COMPLETE WALKTHROUGH", fill=(255, 215, 0), font=f_subpill)

        draw.rectangle((720, 80, 1220, 640), fill=(14, 20, 35), outline=sec_color, width=2)
        draw.text((750, 120), "WHAT YOU LEARN:", fill=(255, 255, 255), font=get_font_for_text("WHAT", 26))

        cy = 190
        for b in (bullets[:5] or ["Core Architecture Explained", "Step-by-Step Implementation", "Production Best Practices", "Live Demo & Source Code"]):
            f_check = get_font_for_text(b, 19)
            draw.text((750, cy), f"⚡ {b[:36]}", fill=(200, 225, 255), font=f_check)
            cy += 65

    draw.rectangle((0, 0, w - 1, h - 1), outline=accent_color, width=3)
    img.save(output_path)
