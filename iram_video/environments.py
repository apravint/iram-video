import random
import math
from PIL import Image, ImageDraw

class EnvironmentRenderer:
    """Renders procedural high-contrast cinematic environments and film sets."""

    @staticmethod
    def render_set(name: str, w: int = 1920, h: int = 1080) -> Image.Image:
        name_clean = name.lower()
        if "quantum" in name_clean or "lab" in name_clean or "server" in name_clean:
            return EnvironmentRenderer.draw_quantum_lab(w, h)
        elif "space" in name_clean or "cosmos" in name_clean or "orbit" in name_clean:
            return EnvironmentRenderer.draw_deep_space(w, h)
        elif "matrix" in name_clean or "grid" in name_clean or "void" in name_clean:
            return EnvironmentRenderer.draw_digital_matrix(w, h)
        else:
            return EnvironmentRenderer.draw_cyberpunk_city(w, h)

    @staticmethod
    def draw_cyberpunk_city(w: int = 1920, h: int = 1080) -> Image.Image:
        """Futuristic cyberpunk observation deck overlooking a sprawling neon city."""
        img = Image.new("RGBA", (w, h), (8, 10, 20, 255))
        draw = ImageDraw.Draw(img)

        # Sky gradient (Midnight blue to violet)
        for y in range(h):
            ratio = y / h
            r = int(6 + 32 * ratio)
            g = int(8 + 8 * ratio)
            b = int(22 + 42 * ratio)
            draw.line([(0, y), (w, y)], fill=(r, g, b, 255))

        # Stars
        rng = random.Random(42)
        for _ in range(140):
            sx, sy = rng.randint(0, w), rng.randint(0, int(h * 0.58))
            draw.ellipse([(sx, sy), (sx + 2, sy + 2)], fill=(180, 220, 255, rng.randint(100, 220)))

        # Distant Skyline Skyscrapers
        for x in range(0, w, 85):
            bh = rng.randint(380, 780)
            bw = rng.randint(70, 130)
            draw.rectangle([(x, h - bh), (x + bw, h)], fill=(14, 18, 34, 255), outline=(28, 42, 75, 255), width=1)
            # Illuminated Windows
            for wy in range(h - bh + 40, h - 80, 24):
                for wx in range(x + 10, x + bw - 14, 18):
                    if rng.random() > 0.42:
                        col = rng.choice([(0, 229, 255, 220), (255, 0, 128, 200), (255, 215, 0, 180), (168, 85, 247, 210)])
                        draw.rectangle([(wx, wy), (wx + 8, wy + 12)], fill=col)

        # Observation Deck Floor
        floor_y = h - 220
        draw.polygon([(0, floor_y), (w, floor_y), (w, h), (0, h)], fill=(12, 16, 28, 255))

        # Perspective Neon Grid Floor
        for gx in range(0, w, 110):
            draw.line([(gx, floor_y), (gx - 90 + int(gx * 0.1), h)], fill=(0, 229, 255, 120), width=2)
        for gy in range(floor_y, h, 32):
            draw.line([(0, gy), (w, gy)], fill=(0, 229, 255, 75), width=1)

        # Holographic Console Table in Center
        draw.polygon([
            (w // 2 - 240, floor_y + 40), (w // 2 + 240, floor_y + 40),
            (w // 2 + 170, floor_y + 110), (w // 2 - 170, floor_y + 110)
        ], fill=(20, 30, 52, 230), outline=(0, 229, 255, 255), width=2)

        # Holographic Projection Beam
        draw.polygon([
            (w // 2 - 120, floor_y + 40), (w // 2 + 120, floor_y + 40),
            (w // 2 + 40, floor_y - 180), (w // 2 - 40, floor_y - 180)
        ], fill=(0, 229, 255, 60))
        draw.ellipse([(w // 2 - 45, floor_y - 195), (w // 2 + 45, floor_y - 165)], outline=(0, 255, 230, 255), width=2)

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
            draw.rectangle([(rx, 140), (rx + rw, h - 180)], fill=(16, 22, 38, 255), outline=(0, 229, 255, 200), width=3)
            # Server blade slots & glowing LEDs
            for slot_y in range(160, h - 200, 36):
                draw.line([(rx + 10, slot_y), (rx + rw - 10, slot_y)], fill=(30, 42, 68, 255), width=2)
                for led_x in range(rx + 20, rx + 120, 20):
                    led_c = (0, 255, 136, 255) if (slot_y + led_x) % 3 == 0 else (0, 229, 255, 255)
                    draw.ellipse([(led_x, slot_y + 8), (led_x + 6, slot_y + 14)], fill=led_c)

        # Central Cryogenic Core Chandelier (Dilution Refrigerator)
        cx = w // 2
        draw.line([(cx, 100), (cx, 320)], fill=(200, 220, 240, 255), width=18)
        # Gold & Copper Plates
        plates = [
            (320, 180, (212, 175, 55, 255)),
            (420, 140, (184, 115, 51, 255)),
            (500, 100, (212, 175, 55, 255)),
            (570, 60, (0, 229, 255, 255))
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
            draw.line([(fx, floor_y), (fx - 60, h)], fill=(0, 229, 255, 90), width=2)

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
