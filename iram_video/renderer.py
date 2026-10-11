from pathlib import Path
from typing import Dict, Any, List, Tuple
from PIL import Image, ImageDraw, ImageFont

FONT_EN_BOLD = "/home/apravint/.local/share/fonts/JetBrainsMono/JetBrainsMonoNerdFontPropo-Bold.ttf"
FONT_EN_REG = "/home/apravint/.local/share/fonts/JetBrainsMono/JetBrainsMonoNerdFontPropo-Regular.ttf"

FONT_TA_BOLD = "/usr/share/fonts/truetype/noto/NotoSansTamil-Bold.ttf"
FONT_TA_REG = "/usr/share/fonts/truetype/noto/NotoSansTamil-Regular.ttf"

WIDTH, HEIGHT = 1920, 1080

def is_tamil_text(text: str) -> bool:
    return any("\u0b80" <= c <= "\u0bff" for c in str(text))

def get_font_for_text(text: str, size: int, bold: bool = False):
    if is_tamil_text(text):
        p = FONT_TA_BOLD if bold else FONT_TA_REG
    else:
        p = FONT_EN_BOLD if bold else FONT_EN_REG
    try:
        return ImageFont.truetype(p, size)
    except Exception:
        return ImageFont.load_default()

def wrap_text(text: str, font, max_width: int, draw: ImageDraw.Draw) -> List[str]:
    lines = []
    for paragraph in str(text).split("\n"):
        words = paragraph.split(" ")
        cur = []
        for word in words:
            test = " ".join(cur + [word])
            bbox = draw.textbbox((0, 0), test, font=font)
            if (bbox[2] - bbox[0]) <= max_width:
                cur.append(word)
            else:
                if cur:
                    lines.append(" ".join(cur))
                    cur = [word]
                else:
                    lines.append(word)
                    cur = []
        if cur:
            lines.append(" ".join(cur))
    return lines

class SlideRenderer:
    def __init__(self, theme: Dict[str, Any] = None):
        theme = theme or {}
        self.bg_color = tuple(theme.get("bg", [10, 14, 24])) + (255,)
        self.accent_color = tuple(theme.get("accent", [0, 229, 255])) + (255,)
        self.sec_color = tuple(theme.get("secondary", [168, 85, 247])) + (255,)
        self.card_bg = tuple(theme.get("card_bg", [16, 24, 42])) + (235,)

    def create_canvas(self, video_title: str) -> Tuple[Image.Image, ImageDraw.Draw]:
        img = Image.new("RGBA", (WIDTH, HEIGHT), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        # Grid lines
        grid_col = (25, 36, 56, 90)
        for x in range(0, WIDTH, 80):
            draw.line([(x, 0), (x, HEIGHT)], fill=grid_col, width=1)
        for y in range(0, HEIGHT, 80):
            draw.line([(0, y), (WIDTH, y)], fill=grid_col, width=1)

        # Top gradient border
        for x in range(WIDTH):
            r = int(self.accent_color[0] + (self.sec_color[0] - self.accent_color[0]) * (x / WIDTH))
            g = int(self.accent_color[1] + (self.sec_color[1] - self.accent_color[1]) * (x / WIDTH))
            b = int(self.accent_color[2] + (self.sec_color[2] - self.accent_color[2]) * (x / WIDTH))
            draw.line([(x, 0), (x, 5)], fill=(r, g, b, 255), width=5)

        # Bottom status bar
        draw.line([(0, HEIGHT - 45), (WIDTH, HEIGHT - 45)], fill=(30, 44, 70, 255), width=1)
        f_bot = get_font_for_text(video_title, 18, bold=False)
        draw.text((60, HEIGHT - 34), video_title[:80], fill=(120, 145, 180), font=f_bot)
        draw.text((WIDTH - 240, HEIGHT - 34), "IRAM AI Video", fill=self.accent_color, font=get_font_for_text("IRAM", 18, bold=True))
        return img, draw

    def draw_card_frame(self, img: Image.Image, box: Tuple[int, int, int, int], title: str, subtitle: str = "", border_color = None) -> Tuple[int, int, int, int]:
        draw = ImageDraw.Draw(img)
        bcol = border_color or self.accent_color
        x1, y1, x2, y2 = box
        draw.rectangle(box, fill=self.card_bg, outline=bcol, width=2)
        
        head_h = 56 if not subtitle else 78
        draw.line([(x1, y1 + head_h), (x2, y1 + head_h)], fill=bcol, width=1)
        f_title = get_font_for_text(title, 22, bold=True)
        draw.text((x1 + 20, y1 + 14), title[:50], fill=(255, 255, 255), font=f_title)
        if subtitle:
            f_sub = get_font_for_text(subtitle, 15, bold=False)
            draw.text((x1 + 20, y1 + 46), subtitle[:65], fill=(130, 160, 200), font=f_sub)
        return (x1 + 20, y1 + head_h + 16, x2 - 20, y2 - 16)

    def render_scene(self, scene: Dict[str, Any], video_title: str, out_path: Path):
        img, draw = self.create_canvas(video_title)
        
        heading = scene.get("heading", "OVERVIEW")
        subheading = scene.get("subheading", "")
        f_head = get_font_for_text(heading, 44, bold=True)
        f_subhead = get_font_for_text(subheading, 22, bold=False)
        
        draw.text((100, 50), heading[:65], fill=(255, 255, 255), font=f_head)
        draw.text((100, 105), subheading[:95], fill=self.accent_color, font=f_subhead)

        l_type = scene.get("layout_type", "pillars")
        cards = scene.get("cards", [])

        if l_type == "comparison" or len(cards) == 2:
            self._render_comparison(img, cards)
        elif l_type == "code_or_terminal":
            self._render_terminal(img, cards, heading)
        elif l_type == "stack_list" or len(cards) >= 4:
            self._render_stack_list(img, cards)
        elif l_type == "hero_metric":
            self._render_hero_metric(img, cards)
        else:
            self._render_pillars(img, cards)

        img.save(out_path)

    def _render_pillars(self, img: Image.Image, cards: List[Dict[str, Any]]):
        num = max(1, min(3, len(cards)))
        card_w = (1720 - (num - 1) * 40) // num
        card_y, card_h = 180, 700
        start_x = 100

        for i, card in enumerate(cards[:3]):
            x = start_x + i * (card_w + 40)
            col = self.accent_color if i % 2 == 0 else self.sec_color
            ib = self.draw_card_frame(img, (x, card_y, x + card_w, card_y + card_h), card.get("title", ""), card.get("subtitle", ""), border_color=col)
            cdraw = ImageDraw.Draw(img)
            
            badge = card.get("badge")
            by = ib[1]
            if badge:
                f_badge = get_font_for_text(badge, 15, bold=True)
                cdraw.rectangle((ib[0], by, ib[0] + 160, by + 34), fill=(25, 38, 60), outline=col, width=1)
                cdraw.text((ib[0] + 12, by + 6), badge, fill=col, font=f_badge)
                by += 50
                
            for bullet in card.get("bullets", []):
                f_bullet = get_font_for_text(bullet, 17, bold=False)
                wrapped = wrap_text(bullet, f_bullet, card_w - 40, cdraw)
                for w in wrapped:
                    cdraw.text((ib[0], by), f"• {w}", fill=(190, 215, 240), font=f_bullet)
                    by += 25
                by += 12

    def _render_comparison(self, img: Image.Image, cards: List[Dict[str, Any]]):
        col_w = 830
        card_y, card_h = 180, 700
        cols = [self.accent_color, self.sec_color]
        positions = [100, 990]

        for i, card in enumerate(cards[:2]):
            x = positions[i]
            col = cols[i]
            ib = self.draw_card_frame(img, (x, card_y, x + col_w, card_y + card_h), card.get("title", ""), card.get("subtitle", ""), border_color=col)
            cdraw = ImageDraw.Draw(img)
            by = ib[1]
            for bullet in card.get("bullets", []):
                f_b = get_font_for_text(bullet, 18, bold=False)
                cdraw.text((ib[0], by), "✓", fill=col, font=get_font_for_text("✓", 20, bold=True))
                wrapped = wrap_text(bullet, f_b, col_w - 50, cdraw)
                for w in wrapped:
                    cdraw.text((ib[0] + 28, by), w, fill=(195, 215, 240), font=f_b)
                    by += 26
                by += 16

    def _render_terminal(self, img: Image.Image, cards: List[Dict[str, Any]], heading: str):
        ib = self.draw_card_frame(img, (100, 180, WIDTH - 100, 900), "Terminal / Code Simulation", heading, border_color=(0, 255, 136, 200))
        tdraw = ImageDraw.Draw(img)
        ty = ib[1] + 10
        
        for card in cards:
            title = card.get("title", "")
            if title:
                f_t = get_font_for_text(title, 20, bold=True)
                tdraw.text((ib[0] + 10, ty), f"$ {title}", fill=(0, 255, 136), font=f_t)
                ty += 34
            for b in card.get("bullets", []):
                f_term = get_font_for_text(b, 18, bold=False)
                tdraw.text((ib[0] + 25, ty), f"> {b}", fill=(200, 225, 255), font=f_term)
                ty += 28
            ty += 16

    def _render_stack_list(self, img: Image.Image, cards: List[Dict[str, Any]]):
        y = 180
        card_h = 155
        for i, card in enumerate(cards[:4]):
            col = self.accent_color if i % 2 == 0 else self.sec_color
            ib = self.draw_card_frame(img, (100, y, WIDTH - 100, y + card_h), card.get("title", ""), card.get("subtitle", ""), border_color=col)
            sdraw = ImageDraw.Draw(img)
            bullets_text = "  |  ".join(card.get("bullets", []))
            f_desc = get_font_for_text(bullets_text, 18, bold=False)
            wrapped = wrap_text(bullets_text, f_desc, WIDTH - 260, sdraw)
            dy = ib[1] + 6
            for w in wrapped:
                sdraw.text((ib[0], dy), w, fill=(195, 215, 240), font=f_desc)
                dy += 26
            y += 175

    def _render_hero_metric(self, img: Image.Image, cards: List[Dict[str, Any]]):
        card1 = cards[0] if cards else {}
        ib1 = self.draw_card_frame(img, (100, 180, 720, 880), card1.get("title", "HIGHLIGHT"), "", border_color=self.accent_color)
        c1_draw = ImageDraw.Draw(img)
        f_hero = get_font_for_text(card1.get("badge", "★ 100%"), 60, bold=True)
        c1_draw.text((ib1[0] + 20, ib1[1] + 40), card1.get("badge", "★ 100%"), fill=self.accent_color, font=f_hero)
        hy = ib1[1] + 160
        for b in card1.get("bullets", []):
            f_b = get_font_for_text(b, 18, bold=False)
            wrapped = wrap_text(b, f_b, 540, c1_draw)
            for w in wrapped:
                c1_draw.text((ib1[0] + 20, hy), f"• {w}", fill=(190, 215, 240), font=f_b)
                hy += 26
            hy += 14

        card2 = cards[1] if len(cards) > 1 else {}
        ib2 = self.draw_card_frame(img, (760, 180, WIDTH - 100, 880), card2.get("title", "BREAKDOWN"), card2.get("subtitle", ""), border_color=self.sec_color)
        c2_draw = ImageDraw.Draw(img)
        ry = ib2[1]
        for b in card2.get("bullets", []):
            f_b = get_font_for_text(b, 18, bold=False)
            wrapped = wrap_text(b, f_b, 980, c2_draw)
            for w in wrapped:
                c2_draw.text((ib2[0] + 20, ry), f"✓ {w}", fill=(190, 215, 240), font=f_b)
                ry += 26
            ry += 16
