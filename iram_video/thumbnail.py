from pathlib import Path
from typing import Dict, Any, List
from PIL import Image, ImageDraw, ImageFont

FONT_BOLD_PATH = "/home/apravint/.local/share/fonts/JetBrainsMono/JetBrainsMonoNerdFontPropo-Bold.ttf"
W, H = 1280, 720

def get_font(size: int):
    try:
        return ImageFont.truetype(FONT_BOLD_PATH, size)
    except Exception:
        return ImageFont.load_default()

def generate_thumbnail(title: str, bullets: List[str], theme: Dict[str, Any], output_path: Path):
    bg_color = tuple(theme.get("bg", [10, 14, 24])) + (255,)
    accent_color = tuple(theme.get("accent", [0, 229, 255])) + (255,)
    sec_color = tuple(theme.get("secondary", [168, 85, 247])) + (255,)

    img = Image.new("RGBA", (W, H), bg_color)
    draw = ImageDraw.Draw(img)

    # Top accent line
    for x in range(W):
        r = int(accent_color[0] + (sec_color[0] - accent_color[0]) * (x / W))
        g = int(accent_color[1] + (sec_color[1] - accent_color[1]) * (x / W))
        b = int(accent_color[2] + (sec_color[2] - accent_color[2]) * (x / W))
        draw.line([(x, 0), (x, 6)], fill=(r, g, b, 255), width=6)

    # Left Hero Box
    draw.rectangle((60, 80, 680, 640), fill=(16, 24, 42), outline=accent_color, width=3)
    
    # Category Pill
    draw.rectangle((90, 120, 380, 170), fill=(220, 38, 38))
    draw.text((110, 132), "★ FEATURED GUIDE", fill=(255, 255, 255), font=get_font(22))

    # Big Title split
    words = title.upper().split(" ")
    mid = max(1, len(words) // 2)
    line1 = " ".join(words[:mid])
    line2 = " ".join(words[mid:])

    draw.text((90, 210), line1[:25], fill=(255, 255, 255), font=get_font(52))
    draw.text((90, 280), line2[:28], fill=accent_color, font=get_font(56))

    # Callout pill
    draw.rectangle((90, 380, 650, 440), fill=(24, 36, 60), outline=sec_color, width=2)
    draw.text((110, 396), "COMPLETE WALKTHROUGH", fill=(255, 215, 0), font=get_font(24))

    # Right Side Checklist Box
    draw.rectangle((720, 80, 1220, 640), fill=(14, 20, 35), outline=sec_color, width=2)
    draw.text((750, 120), "WHAT YOU LEARN:", fill=(255, 255, 255), font=get_font(26))

    cy = 190
    f_check = get_font(20)
    for b in (bullets[:5] or ["Core Architecture Explained", "Step-by-Step Implementation", "Production Best Practices", "Live Demo & Source Code"]):
        draw.text((750, cy), f"⚡ {b[:38]}", fill=(200, 225, 255), font=f_check)
        cy += 65

    # Overall border
    draw.rectangle((0, 0, W - 1, H - 1), outline=accent_color, width=3)
    img.save(output_path)
