import random
import math
from PIL import Image, ImageDraw

class EnvironmentRenderer:
    """Renders procedural high-contrast cinematic environments and film sets."""

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
        """High-end minimalist creator studio: acoustic wood slat wall, soft diffused backlight, executive desk."""
        img = Image.new("RGBA", (w, h), (15, 23, 42, 255))
        draw = ImageDraw.Draw(img)

        # Back Wall Gradient (Deep slate to charcoal)
        for y in range(h):
            ratio = y / h
            r = int(15 + 10 * ratio)
            g = int(23 + 12 * ratio)
            b = int(42 + 15 * ratio)
            draw.line([(0, y), (w, y)], fill=(r, g, b, 255))

        # Vertical Warm Acoustic Wood Slat Panels across background
        slat_w = 18
        gap_w = 12
        for x in range(60, w - 60, slat_w + gap_w):
            # Rich warm natural walnut / oak tones
            draw.rectangle([(x, 80), (x + slat_w, h - 220)], fill=(92, 64, 46, 255), outline=(58, 40, 28, 255), width=1)
            # Wood grain highlight streak
            draw.line([(x + 4, 80), (x + 4, h - 220)], fill=(120, 85, 60, 180), width=2)

        # Soft Warm Diffused Studio Backlight Glow behind subject area
        cx, cy = w // 2, int(h * 0.45)
        for rad in range(380, 40, -30):
            alpha = int(22 * (1.0 - rad / 380))
            draw.ellipse([(cx - rad, cy - rad), (cx + rad, cy + rad)], fill=(245, 158, 11, alpha))

        # Executive Matte Black / Walnut Studio Desk in Foreground
        floor_y = h - 220
        draw.polygon([(0, floor_y), (w, floor_y), (w, h), (0, h)], fill=(24, 30, 42, 255))
        # Sleek desk chamfer edge
        draw.line([(0, floor_y), (w, floor_y)], fill=(71, 85, 105, 255), width=3)
        draw.line([(0, floor_y + 4), (w, floor_y + 4)], fill=(30, 41, 59, 255), width=2)

        # Subtle warm reflection on desk surface
        draw.ellipse([(cx - 260, floor_y + 10), (cx + 260, floor_y + 70)], fill=(245, 158, 11, 18))

        return img

    @staticmethod
    def draw_executive_boardroom(w: int = 1920, h: int = 1080) -> Image.Image:
        """Executive boardroom overlooking modern twilight city skyline through floor-to-ceiling glass."""
        img = Image.new("RGBA", (w, h), (15, 23, 42, 255))
        draw = ImageDraw.Draw(img)

        # Dusk sky gradient (deep navy to warm dusk horizon)
        for y in range(h):
            ratio = y / h
            r = int(12 + 25 * ratio)
            g = int(18 + 15 * ratio)
            b = int(36 + 20 * ratio)
            draw.line([(0, y), (w, y)], fill=(r, g, b, 255))

        # Distant modern skyscrapers with natural warm incandescent window lights
        rng = random.Random(101)
        for x in range(0, w, 90):
            bh = rng.randint(340, 700)
            bw = rng.randint(75, 125)
            draw.rectangle([(x, h - bh), (x + bw, h)], fill=(20, 28, 45, 255), outline=(35, 48, 75, 255), width=1)
            for wy in range(h - bh + 40, h - 180, 26):
                for wx in range(x + 12, x + bw - 14, 20):
                    if rng.random() > 0.45:
                        w_col = rng.choice([(255, 220, 140, 200), (230, 240, 255, 180), (255, 195, 100, 190)])
                        draw.rectangle([(wx, wy), (wx + 8, wy + 12)], fill=w_col)

        # Architectural Glass Mullions (Floor-to-Ceiling Windows)
        floor_y = h - 220
        for mx in [360, 760, 1160, 1560]:
            draw.line([(mx, 0), (mx, floor_y)], fill=(30, 41, 59, 255), width=10)
            draw.line([(mx, 0), (mx, floor_y)], fill=(51, 65, 85, 255), width=2)

        # Executive conference desk
        draw.polygon([(0, floor_y), (w, floor_y), (w, h), (0, h)], fill=(20, 26, 38, 255))
        draw.line([(0, floor_y), (w, floor_y)], fill=(71, 85, 105, 255), width=3)

        return img

    @staticmethod
    def draw_cyberpunk_city(w: int = 1920, h: int = 1080) -> Image.Image:
        """Modern metropolitan skyline with architectural illumination (clean, sophisticated)."""
        img = Image.new("RGBA", (w, h), (15, 23, 42, 255))
        draw = ImageDraw.Draw(img)

        # Sky gradient (Midnight blue)
        for y in range(h):
            ratio = y / h
            r = int(10 + 15 * ratio)
            g = int(14 + 18 * ratio)
            b = int(28 + 30 * ratio)
            draw.line([(0, y), (w, y)], fill=(r, g, b, 255))

        # Stars
        rng = random.Random(42)
        for _ in range(140):
            sx, sy = rng.randint(0, w), rng.randint(0, int(h * 0.58))
            draw.ellipse([(sx, sy), (sx + 2, sy + 2)], fill=(200, 225, 255, rng.randint(80, 180)))

        # Distant Skyline Skyscrapers
        for x in range(0, w, 85):
            bh = rng.randint(380, 780)
            bw = rng.randint(70, 130)
            draw.rectangle([(x, h - bh), (x + bw, h)], fill=(20, 28, 44, 255), outline=(35, 48, 75, 255), width=1)
            # Illuminated Windows: Warm architectural light & clean white (NO neon pink/magenta)
            for wy in range(h - bh + 40, h - 80, 24):
                for wx in range(x + 10, x + bw - 14, 18):
                    if rng.random() > 0.42:
                        col = rng.choice([(255, 220, 140, 200), (220, 235, 255, 180), (255, 195, 90, 190), (148, 163, 184, 170)])
                        draw.rectangle([(wx, wy), (wx + 8, wy + 12)], fill=col)

        # Observation Deck Floor
        floor_y = h - 220
        draw.polygon([(0, floor_y), (w, floor_y), (w, h), (0, h)], fill=(24, 32, 48, 255))

        # Clean architectural perspective floor
        for gx in range(0, w, 110):
            draw.line([(gx, floor_y), (gx - 90 + int(gx * 0.1), h)], fill=(51, 65, 85, 80), width=1)
        for gy in range(floor_y, h, 32):
            draw.line([(0, gy), (w, gy)], fill=(51, 65, 85, 60), width=1)

        # Executive Console Table in Center
        draw.polygon([
            (w // 2 - 240, floor_y + 40), (w // 2 + 240, floor_y + 40),
            (w // 2 + 170, floor_y + 110), (w // 2 - 170, floor_y + 110)
        ], fill=(30, 41, 59, 230), outline=(71, 85, 105, 255), width=2)

        return img

    @staticmethod
    def draw_quantum_lab(w: int = 1920, h: int = 1080) -> Image.Image:
        """Futuristic Quantum Supercomputer Research Facility."""
        img = Image.new("RGBA", (w, h), (10, 12, 22, 255))
        draw = ImageDraw.Draw(img)

        # Back Wall Gradient
        for y in range(h):
            c = int(10 + 18 * (y / h))
            draw.line([(0, y), (w, y)], fill=(c, c + 4, c + 14, 255))

        # Quantum Computing Racks (Left & Right flanking pillars)
        for rx, rw in [(120, 260), (w - 380, 260)]:
            draw.rectangle([(rx, 140), (rx + rw, h - 180)], fill=(16, 22, 38, 255), outline=(59, 130, 246, 200), width=2)
            # Server blade slots & subtle status LEDs
            for slot_y in range(160, h - 200, 36):
                draw.line([(rx + 10, slot_y), (rx + rw - 10, slot_y)], fill=(30, 42, 68, 255), width=2)
                for led_x in range(rx + 20, rx + 120, 20):
                    led_c = (59, 130, 246, 255) if (slot_y + led_x) % 3 == 0 else (245, 158, 11, 255)
                    draw.ellipse([(led_x, slot_y + 8), (led_x + 6, slot_y + 14)], fill=led_c)

        # Central Cryogenic Core Chandelier (Dilution Refrigerator)
        cx = w // 2
        draw.line([(cx, 100), (cx, 320)], fill=(200, 220, 240, 255), width=18)
        # Gold & Copper Plates
        plates = [
            (320, 180, (212, 175, 55, 255)),
            (420, 140, (184, 115, 51, 255)),
            (500, 100, (212, 175, 55, 255)),
            (570, 60, (59, 130, 246, 255))
        ]
        for py, pw, pcol in plates:
            draw.ellipse([(cx - pw, py - 20), (cx + pw, py + 20)], fill=pcol, outline=(255, 255, 255, 220), width=2)
            # Vertical cryogenic coils
            draw.line([(cx - pw + 20, py), (cx - pw + 20, py + 60)], fill=(184, 115, 51, 255), width=4)
            draw.line([(cx + pw - 20, py), (cx + pw - 20, py + 60)], fill=(184, 115, 51, 255), width=4)

        # Floor with reflections
        floor_y = h - 200
        draw.rectangle([(0, floor_y), (w, h)], fill=(8, 12, 20, 255))
        for fx in range(0, w, 140):
            draw.line([(fx, floor_y), (fx - 60, h)], fill=(51, 65, 85, 90), width=2)

        return img

    @staticmethod
    def draw_deep_space(w: int = 1920, h: int = 1080) -> Image.Image:
        """Deep Space Odyssey with Planetary Horizon and Glowing Nebula."""
        img = Image.new("RGBA", (w, h), (4, 6, 14, 255))
        draw = ImageDraw.Draw(img)

        # Nebula clouds
        for nx, ny, nr, ncol in [
            (450, 350, 320, (168, 85, 247, 45)),
            (1450, 300, 360, (0, 229, 255, 40)),
            (950, 480, 280, (236, 72, 153, 35))
        ]:
            for r_step in range(nr, 20, -30):
                draw.ellipse([(nx - r_step, ny - r_step), (nx + r_step, ny + r_step)], fill=ncol)

        # Starfield
        rng = random.Random(1337)
        for _ in range(250):
            sx, sy = rng.randint(0, w), rng.randint(0, h)
            draw.ellipse([(sx, sy), (sx + rng.randint(1, 3), sy + rng.randint(1, 3))], fill=(255, 255, 255, rng.randint(120, 255)))

        # Giant Planetary Ring Arc on Right
        px, py = w - 100, h + 300
        pr = 700
        draw.ellipse([(px - pr, py - pr), (px + pr, py + pr)], fill=(18, 30, 60, 255), outline=(0, 229, 255, 255), width=4)
        # Ring System
        draw.arc([(px - pr - 250, py - pr - 180), (px + pr + 250, py + pr + 180)], start=160, end=340, fill=(212, 175, 55, 180), width=16)

        # Spaceship Bridge Horizon Floor
        floor_y = h - 220
        draw.polygon([(0, floor_y), (w, floor_y), (w, h), (0, h)], fill=(12, 16, 26, 255))
        draw.line([(0, floor_y), (w, floor_y)], fill=(0, 229, 255, 255), width=3)
        # Bridge Window Struts
        for wx in [380, 800, 1120, 1540]:
            draw.line([(wx, 0), (wx - 60, floor_y)], fill=(30, 44, 70, 255), width=12)
            draw.line([(wx, 0), (wx - 60, floor_y)], fill=(0, 229, 255, 180), width=2)

        return img

    @staticmethod
    def draw_digital_matrix(w: int = 1920, h: int = 1080) -> Image.Image:
        """The Matrix Cyberspace Void with Cascading Digital Streams."""
        img = Image.new("RGBA", (w, h), (4, 10, 8, 255))
        draw = ImageDraw.Draw(img)

        # Digital Rain streams
        rng = random.Random(777)
        for col_x in range(0, w, 24):
            length = rng.randint(8, 28)
            start_y = rng.randint(-100, h - 300)
            for char_i in range(length):
                cy = start_y + char_i * 22
                if 0 <= cy <= h:
                    alpha = int(255 * (char_i / length))
                    col = (0, 255, 100, alpha) if char_i == length - 1 else (0, 200, 70, alpha // 2)
                    draw.rectangle([(col_x, cy), (col_x + 8, cy + 14)], fill=col)

        # Horizon Grid Wireframe
        floor_y = h - 240
        draw.polygon([(0, floor_y), (w, floor_y), (w, h), (0, h)], fill=(2, 14, 6, 255))
        for gx in range(0, w, 90):
            draw.line([(gx, floor_y), (gx - 100 + int(gx * 0.12), h)], fill=(0, 255, 136, 180), width=2)
        for gy in range(floor_y, h, 30):
            draw.line([(0, gy), (w, gy)], fill=(0, 255, 136, 120), width=1)

        return img
