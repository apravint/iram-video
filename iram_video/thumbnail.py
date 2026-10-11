from pathlib import Path
from typing import Dict, Any, List, Tuple
from PIL import Image, ImageDraw, ImageFont

from .renderer import get_fonts, draw_mixed_line, split_runs, get_mixed_width

def generate_thumbnail(title: str, bullets: List[str], theme: Dict[str, Any], output_path: Path, is_shorts: bool = False, is_cinema: bool = False, character: Optional[str] = None):
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

    badge_text = "★ CINEMATIC TRAILER" if is_cinema else ("★ YOUTUBE SHORTS" if is_shorts else "★ FEATURED GUIDE")

    if is_shorts:
        # Vertical Shorts Thumbnail Layout (1080x1920)
        draw.rectangle((60, 360, w - 60, 1480), fill=(16, 24, 42), outline=accent_color, width=4)
        draw.rectangle((100, 420, 520, 480), fill=(220, 38, 38))
        fta_cat, fen_cat = get_fonts(24)
        draw_mixed_line(draw, 120, 435, badge_text, (255, 255, 255), fta_cat, fen_cat)

        clean_title = title.replace("#Shorts", "").replace("#shorts", "").strip()
        fta_title, fen_title = get_fonts(50)
        from .renderer import wrap_text
        title_lines = wrap_text(clean_title, fta_title, fen_title, 850, draw)
        
        y = 530
        for i, line in enumerate(title_lines[:2]):
            col = (255, 255, 255) if i == 0 else accent_color
            draw_mixed_line(draw, 100, y, line, col, fta_title, fen_title)
            y += 80

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

        clean_title = title.replace("#Shorts", "").replace("#shorts", "").strip()
        fta_l, fen_l = get_fonts(44)
        from .renderer import wrap_text
        title_lines = wrap_text(clean_title, fta_l, fen_l, 560, draw)
        y = 210
        for i, line in enumerate(title_lines[:2]):
            col = (255, 255, 255) if i == 0 else accent_color
            draw_mixed_line(draw, 90, y, line, col, fta_l, fen_l)
            y += 70

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

    if character and character.lower() not in ["none", "false"]:
        try:
            from .characters import CharacterRenderer
            if is_shorts:
                char_img = CharacterRenderer.render_character(character, w=280, h=360, mouth_open=0.6, eye_state="happy", pointing=True)
                img.paste(char_img, (w - 320, 1100), char_img)
            else:
                char_img = CharacterRenderer.render_character(character, w=260, h=340, mouth_open=0.6, eye_state="happy", pointing=True)
                img.paste(char_img, (w - 300, 360), char_img)
        except Exception:
            pass

    draw.rectangle((0, 0, w - 1, h - 1), outline=accent_color, width=3)
    img.save(output_path)
