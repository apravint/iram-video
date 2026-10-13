import random
import math
from PIL import Image, ImageDraw

class EnvironmentRenderer:
    """Renders procedural high-contrast cinematic environments scaled cleanly for both 16:9 and 9:16 layouts."""

    @staticmethod
    def render_set(name: str, w: int = 1920, h: int = 1080) -> Image.Image:
        name_clean = name.lower()
        if "studio" in name_clean or "podcast" in name_clean or "editorial" in name_clean:
            return EnvironmentRenderer.draw_modern_studio(w, h)
        elif "boardroom" in name_clean or "executive" in name_clean or "campus" in name_clean or "office" in name_clean:
            return EnvironmentRenderer.draw_executive_boardroom(w, h)
        elif "quantum" in name_clean or "lab" in name_clean or "server" in name_clean:
            return EnvironmentRenderer.draw_quantum_lab(w, h)
        elif "space" in name_clean or "cosmos" in name_clean or "orbit" in name_clean:
            return EnvironmentRenderer.draw_deep_space(w, h)
        elif "matrix" in name_clean or "grid" in name_clean or "void" in name_clean:
            return EnvironmentRenderer.draw_digital_matrix(w, h)
        elif "cyberpunk" in name_clean:
            return EnvironmentRenderer.draw_cyberpunk_city(w, h)
        else:
            return EnvironmentRenderer.draw_modern_studio(w, h)

    @staticmethod
    def draw_modern_studio(w: int = 1920, h: int = 1080) -> Image.Image:
        img = Image.new("RGBA", (w, h), (15, 23, 42, 255))
        draw = ImageDraw.Draw(img)
        is_shorts = h > w

        # Back Wall Gradient
        for y in range(h):
            ratio = y / h
            r = int(15 + 10 * ratio)
            g = int(23 + 12 * ratio)
            b = int(42 + 15 * ratio)
            draw.line([(0, y), (w, y)], fill=(r, g, b, 255))

        # Dynamic Scaling Spacers
        floor_y = int(h * 0.76) if is_shorts else h - 220
        slat_w = int(14 * (w / 1080.0)) if is_shorts else 18
        gap_w = int(10 * (w / 1080.0)) if is_shorts else 12
        margin = int(40 * (w / 1080.0)) if is_shorts else 60

        for x in range(margin, w - margin, slat_w + gap_w):
            draw.rectangle([(x, int(h * 0.06)), (x + slat_w, floor_y)], fill=(92, 64, 46, 255), outline=(58, 40, 28, 255), width=1)
            draw.line([(x + max(1, slat_w // 4), int(h * 0.06)), (x + max(1, slat_w // 4), floor_y)], fill=(120, 85, 60, 180), width=2)

        # Soft Studio Backlight Glow
        cx, cy = w // 2, int(h * 0.40) if is_shorts else int(h * 0.45)
        rad_max = int(w * 0.45) if is_shorts else 380
        for rad in range(rad_max, 20, -30):
            alpha = int(24 * (1.0 - rad / rad_max))
            draw.ellipse([(cx - rad, cy - rad), (cx + rad, cy + rad)], fill=(245, 158, 11, alpha))

        # Foreground Desk Structure
        draw.polygon([(0, floor_y), (w, floor_y), (w, h), (0, h)], fill=(24, 30, 42, 255))
        draw.line([(0, floor_y), (w, floor_y)], fill=(71, 85, 105, 255), width=max(2, int(3 * (w / 1920.0))))
        
        # Subtle warm reflection on desk surface
        ref_w = int(w * 0.3)
        draw.ellipse([(cx - ref_w, floor_y + 10), (cx + ref_w, floor_y + 60)], fill=(245, 158, 11, 15))
        return img

    @staticmethod
    def draw_executive_boardroom(w: int = 1920, h: int = 1080) -> Image.Image:
        img = Image.new("RGBA", (w, h), (15, 23, 42, 255))
        draw = ImageDraw.Draw(img)
        is_shorts = h > w

        for y in range(h):
            ratio = y / h
            r = int(12 + 25 * ratio)
            g = int(18 + 15 * ratio)
            b = int(36 + 20 * ratio)
            draw.line([(0, y), (w, y)], fill=(r, g, b, 255))

        rng = random.Random(101)
        floor_y = int(h * 0.76) if is_shorts else h - 220
        
        # Distant Skyline Skyscrapers
        for x in range(0, w, int(60 * (w / 1080.0)) if is_shorts else 90):
            bh = rng.randint(int(h * 0.3), int(h * 0.65))
            bw = rng.randint(int(w * 0.08), int(w * 0.15))
            draw.rectangle([(x, h - bh), (x + bw, h)], fill=(20, 28, 45, 255), outline=(35, 48, 75, 255), width=1)
            for wy in range(max(0, h - bh + 40), floor_y - 40, 26):
                for wx in range(x + 12, x + bw - 14, 20):
                    if rng.random() > 0.45:
                        w_col = rng.choice([(255, 220, 140, 200), (230, 240, 255, 180), (255, 195, 100, 190)])
                        draw.rectangle([(wx, wy), (wx + 8, wy + 12)], fill=w_col)

        # FIX: Compute adaptive column spacers smoothly based on the width factor
        if is_shorts:
            mullions = [int(w * 0.25), int(w * 0.5), int(w * 0.75)]
        else:
            mullions = [int(w * 0.2), int(w * 0.4), int(w * 0.6), int(w * 0.8)]
        for mx in mullions:
            draw.line([(mx, 0), (mx, floor_y)], fill=(30, 41, 59, 255), width=max(4, int(10 * (w / 1920.0))))
            draw.line([(mx, 0), (mx, floor_y)], fill=(51, 65, 85, 255), width=max(1, int(2 * (w / 1920.0))))

        draw.polygon([(0, floor_y), (w, floor_y), (w, h), (0, h)], fill=(20, 26, 38, 255))
        draw.line([(0, floor_y), (w, floor_y)], fill=(71, 85, 105, 255), width=max(2, int(3 * (w / 1920.0))))
        return img

    @staticmethod
    def draw_cyberpunk_city(w: int = 1920, h: int = 1080) -> Image.Image:
        img = Image.new("RGBA", (w, h), (15, 23, 42, 255))
        draw = ImageDraw.Draw(img)
        is_shorts = h > w

        for y in range(h):
            ratio = y / h
            r = int(10 + 15 * ratio)
            g = int(14 + 18 * ratio)
            b = int(28 + 30 * ratio)
            draw.line([(0, y), (w, y)], fill=(r, g, b, 255))

        rng = random.Random(42)
        for _ in range(140):
            sx, sy = rng.randint(0, w), rng.randint(0, int(h * 0.5))
            draw.ellipse([(sx, sy), (sx + 2, sy + 2)], fill=(200, 225, 255, rng.randint(80, 180)))

        floor_y = int(h * 0.76) if is_shorts else h - 220
        step_x = int(60 * (w / 1080.0)) if is_shorts else 85
        
        for x in range(0, w, step_x):
            bh = rng.randint(int(h * 0.35), int(h * 0.70))
            bw = rng.randint(int(w * 0.08), int(w * 0.16))
            draw.rectangle([(x, h - bh), (x + bw, h)], fill=(20, 28, 44, 255), outline=(35, 48, 75, 255), width=1)
            for wy in range(max(0, h - bh + 40), floor_y - 20, 24):
                for wx in range(x + 10, x + bw - 14, 18):
                    if rng.random() > 0.42:
                        col = rng.choice([(255, 220, 140, 200), (220, 235, 255, 180), (255, 195, 90, 190)])
                        draw.rectangle([(wx, wy), (wx + 8, wy + 12)], fill=col)

        draw.polygon([(0, floor_y), (w, floor_y), (w, h), (0, h)], fill=(24, 32, 48, 255))
        return img

    @staticmethod
    def draw_quantum_lab(w: int = 1920, h: int = 1080) -> Image.Image:
        img = Image.new("RGBA", (w, h), (10, 12, 22, 255))
        draw = ImageDraw.Draw(img)
        is_shorts = h > w

        for y in range(h):
            c = int(10 + 18 * (y / h))
            draw.line([(0, y), (w, y)], fill=(c, c + 4, c + 14, 255))

        floor_y = int(h * 0.8) if is_shorts else h - 200
        rack_w = int(w * 0.22) if is_shorts else 260
        flanks = [(int(w * 0.05), rack_w), (w - int(w * 0.05) - rack_w, rack_w)]

        for rx, rw in flanks:
            draw.rectangle([(rx, int(h * 0.15)), (rx + rw, floor_y - 20)], fill=(16, 22, 38, 255), outline=(59, 130, 246, 200), width=2)
            for slot_y in range(int(h * 0.18), floor_y - 40, 36):
                draw.line([(rx + 10, slot_y), (rx + rw - 10, slot_y)], fill=(30, 42, 68, 255), width=2)

        cx = w // 2
        draw.line([(cx, int(h * 0.08)), (cx, int(h * 0.3))], fill=(200, 220, 240, 255), width=max(6, int(18 * (w / 1920.0))))
        draw.rectangle([(0, floor_y), (w, h)], fill=(8, 12, 20, 255))
        return img

    @staticmethod
    def draw_deep_space(w: int = 1920, h: int = 1080) -> Image.Image:
        img = Image.new("RGBA", (w, h), (4, 6, 14, 255))
        draw = ImageDraw.Draw(img)
        is_shorts = h > w

        # Nebulae
        for nx, ny, nr, ncol in [
            (int(w * 0.25), int(h * 0.3), int(w * 0.25), (168, 85, 247, 45)),
            (int(w * 0.75), int(h * 0.25), int(w * 0.3), (0, 229, 255, 40))
        ]:
            for r_step in range(nr, 20, -30):
                draw.ellipse([(nx - r_step, ny - r_step), (nx + r_step, ny + r_step)], fill=ncol)

        rng = random.Random(1337)
        for _ in range(180):
            sx, sy = rng.randint(0, w), rng.randint(0, h)
            draw.ellipse([(sx, sy), (sx + 1, sy + 1)], fill=(255, 255, 255, rng.randint(120, 255)))

        floor_y = int(h * 0.76) if is_shorts else h - 220
        draw.polygon([(0, floor_y), (w, floor_y), (w, h), (0, h)], fill=(12, 16, 26, 255))
        draw.line([(0, floor_y), (w, floor_y)], fill=(0, 229, 255, 255), width=3)
        return img

    @staticmethod
    def draw_digital_matrix(w: int = 1920, h: int = 1080) -> Image.Image:
        img = Image.new("RGBA", (w, h), (4, 10, 8, 255))
        draw = ImageDraw.Draw(img)
        is_shorts = h > w

        rng = random.Random(777)
        for col_x in range(0, w, 24):
            length = rng.randint(8, 24)
            start_y = rng.randint(-100, h - 300)
            for char_i in range(length):
                cy = start_y + char_i * 22
                if 0 <= cy <= h:
                    alpha = int(255 * (char_i / length))
                    col = (0, 255, 100, alpha) if char_i == length - 1 else (0, 200, 70, alpha // 2)
                    draw.rectangle([(col_x, cy), (col_x + 6, cy + 12)], fill=col)

        floor_y = int(h * 0.76) if is_shorts else h - 240
        draw.polygon([(0, floor_y), (w, floor_y), (w, h), (0, h)], fill=(2, 14, 6, 255))
        return img
