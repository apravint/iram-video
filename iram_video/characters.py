import math
from typing import Tuple, Optional
from PIL import Image, ImageDraw

class CharacterRenderer:
    """Renders 2D animated mascot and presenter characters with multiple emotional states."""
    
    @staticmethod
    def draw_robot(
        w: int = 400,
        h: int = 500,
        mouth_open: float = 0.0,
        eye_state: str = "normal",
        pointing: bool = True,
        bob_offset: int = 0
    ) -> Image.Image:
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cx = w // 2
        cy_shift = bob_offset

        # Antenna
        draw.line([(cx, 70 + cy_shift), (cx, 30 + cy_shift)], fill=(0, 229, 255, 255), width=6)
        draw.ellipse([(cx - 12, 18 + cy_shift), (cx + 12, 42 + cy_shift)], fill=(0, 255, 200, 255), outline=(255, 255, 255, 255), width=2)

        # Head Chassis
        head_box = (cx - 100, 70 + cy_shift, cx + 100, 210 + cy_shift)
        draw.rounded_rectangle(head_box, radius=35, fill=(20, 28, 48, 255), outline=(0, 229, 255, 255), width=5)

        # Face Display
        screen_box = (cx - 80, 90 + cy_shift, cx + 80, 190 + cy_shift)
        draw.rounded_rectangle(screen_box, radius=20, fill=(8, 12, 22, 255), outline=(0, 160, 255, 180), width=2)

        # Glowing Eyes
        if eye_state == "blink":
            draw.line([(cx - 55, 130 + cy_shift), (cx - 25, 130 + cy_shift)], fill=(0, 255, 230, 255), width=4)
            draw.line([(cx + 25, 130 + cy_shift), (cx + 55, 130 + cy_shift)], fill=(0, 255, 230, 255), width=4)
        elif eye_state == "happy":
            draw.arc([(cx - 60, 110 + cy_shift), (cx - 20, 145 + cy_shift)], start=180, end=360, fill=(0, 255, 230, 255), width=5)
            draw.arc([(cx + 20, 110 + cy_shift), (cx + 60, 145 + cy_shift)], start=180, end=360, fill=(0, 255, 230, 255), width=5)
        else: # normal
            draw.ellipse([(cx - 55, 115 + cy_shift), (cx - 25, 145 + cy_shift)], fill=(0, 255, 230, 255))
            draw.ellipse([(cx + 25, 115 + cy_shift), (cx + 55, 145 + cy_shift)], fill=(0, 255, 230, 255))
            draw.ellipse([(cx - 45, 120 + cy_shift), (cx - 35, 130 + cy_shift)], fill=(255, 255, 255, 255))
            draw.ellipse([(cx + 35, 120 + cy_shift), (cx + 45, 130 + cy_shift)], fill=(255, 255, 255, 255))

        # Animated Digital Mouth
        m_w = 42
        m_h = max(5, int(6 + mouth_open * 20))
        my = 166 + cy_shift
        draw.rounded_rectangle([(cx - m_w // 2, my - m_h // 2), (cx + m_w // 2, my + m_h // 2)], radius=m_h // 2, fill=(0, 255, 180, 255))

        # Torso
        body_box = (cx - 75, 225 + cy_shift, cx + 75, 380 + cy_shift)
        draw.rounded_rectangle(body_box, radius=25, fill=(16, 24, 42, 255), outline=(0, 229, 255, 255), width=4)
        draw.ellipse([(cx - 20, 260 + cy_shift), (cx + 20, 300 + cy_shift)], fill=(0, 229, 255, 255), outline=(255, 255, 255, 255), width=3)

        # Arms
        if pointing:
            # Left arm pointing towards presentation
            draw.line([(cx - 75, 250 + cy_shift), (cx - 150, 180 + cy_shift)], fill=(0, 229, 255, 255), width=16)
            draw.ellipse([(cx - 165, 165 + cy_shift), (cx - 135, 195 + cy_shift)], fill=(0, 255, 200, 255))
            # Right arm down
            draw.line([(cx + 75, 250 + cy_shift), (cx + 120, 330 + cy_shift)], fill=(0, 229, 255, 255), width=16)
            draw.ellipse([(cx + 105, 315 + cy_shift), (cx + 135, 345 + cy_shift)], fill=(0, 255, 200, 255))
        else:
            draw.line([(cx - 75, 250 + cy_shift), (cx - 120, 330 + cy_shift)], fill=(0, 229, 255, 255), width=16)
            draw.ellipse([(cx - 135, 315 + cy_shift), (cx - 105, 345 + cy_shift)], fill=(0, 255, 200, 255))
            draw.line([(cx + 75, 250 + cy_shift), (cx + 120, 330 + cy_shift)], fill=(0, 229, 255, 255), width=16)
            draw.ellipse([(cx + 105, 315 + cy_shift), (cx + 135, 345 + cy_shift)], fill=(0, 255, 200, 255))

        return img

    @staticmethod
    def draw_ferris(
        w: int = 400,
        h: int = 400,
        mouth_open: float = 0.0,
        eye_state: str = "normal",
        pointing: bool = True,
        bob_offset: int = 0
    ) -> Image.Image:
        """Draws Ferris the Rust Crab mascot."""
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cx = w // 2
        cy = h // 2 + bob_offset

        # Crab Body (Orange-red shell)
        shell_box = (cx - 110, cy - 60, cx + 110, cy + 90)
        draw.ellipse(shell_box, fill=(235, 78, 38, 255), outline=(180, 40, 15, 255), width=4)

        # Legs (3 on left, 3 on right)
        for offset in [-30, 0, 30]:
            draw.line([(cx - 100, cy + offset), (cx - 145, cy + offset + 25)], fill=(210, 60, 25, 255), width=7)
            draw.line([(cx + 100, cy + offset), (cx + 145, cy + offset + 25)], fill=(210, 60, 25, 255), width=7)

        # Claws
        if pointing:
            # Left claw raised high
            draw.line([(cx - 80, cy - 30), (cx - 130, cy - 90)], fill=(235, 78, 38, 255), width=14)
            draw.arc([(cx - 160, cy - 120), (cx - 110, cy - 70)], start=30, end=300, fill=(235, 78, 38, 255), width=10)
            # Right claw normal
            draw.line([(cx + 80, cy - 20), (cx + 130, cy - 50)], fill=(235, 78, 38, 255), width=14)
            draw.arc([(cx + 110, cy - 80), (cx + 160, cy - 30)], start=120, end=30, fill=(235, 78, 38, 255), width=10)
        else:
            draw.line([(cx - 80, cy - 20), (cx - 130, cy - 60)], fill=(235, 78, 38, 255), width=14)
            draw.arc([(cx - 160, cy - 90), (cx - 110, cy - 40)], start=30, end=300, fill=(235, 78, 38, 255), width=10)
            draw.line([(cx + 80, cy - 20), (cx + 130, cy - 60)], fill=(235, 78, 38, 255), width=14)
            draw.arc([(cx + 110, cy - 90), (cx + 160, cy - 40)], start=120, end=30, fill=(235, 78, 38, 255), width=10)

        # Stalk Eyes
        draw.line([(cx - 45, cy - 55), (cx - 50, cy - 95)], fill=(235, 78, 38, 255), width=9)
        draw.line([(cx + 45, cy - 55), (cx + 50, cy - 95)], fill=(235, 78, 38, 255), width=9)

        eye_l = (cx - 70, cy - 120, cx - 30, cy - 80)
        eye_r = (cx + 30, cy - 120, cx + 70, cy - 80)
        draw.ellipse(eye_l, fill=(255, 255, 255, 255), outline=(180, 40, 15, 255), width=3)
        draw.ellipse(eye_r, fill=(255, 255, 255, 255), outline=(180, 40, 15, 255), width=3)

        if eye_state == "blink":
            draw.line([(cx - 65, cy - 100), (cx - 35, cy - 100)], fill=(40, 20, 15, 255), width=4)
            draw.line([(cx + 35, cy - 100), (cx + 65, cy - 100)], fill=(40, 20, 15, 255), width=4)
        else:
            # Black pupils
            draw.ellipse([(cx - 55, cy - 105), (cx - 40, cy - 90)], fill=(30, 20, 20, 255))
            draw.ellipse([(cx + 45, cy - 105), (cx + 60, cy - 90)], fill=(30, 20, 20, 255))
            # Catchlight
            draw.ellipse([(cx - 52, cy - 103), (cx - 46, cy - 97)], fill=(255, 255, 255, 255))
            draw.ellipse([(cx + 48, cy - 103), (cx + 54, cy - 97)], fill=(255, 255, 255, 255))

        # Mouth
        m_w = 40
        m_h = max(4, int(6 + mouth_open * 22))
        my = cy + 25
        draw.rounded_rectangle([(cx - m_w // 2, my - m_h // 2), (cx + m_w // 2, my + m_h // 2)], radius=m_h // 2, fill=(120, 25, 10, 255))

        return img

    @staticmethod
    def draw_gopher(
        w: int = 400,
        h: int = 450,
        mouth_open: float = 0.0,
        eye_state: str = "normal",
        pointing: bool = True,
        bob_offset: int = 0
    ) -> Image.Image:
        """Draws the Go Gopher mascot."""
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cx = w // 2
        cy = h // 2 + bob_offset

        # Gopher Blue Body
        gopher_blue = (0, 173, 216, 255)
        body_box = (cx - 95, cy - 110, cx + 95, cy + 130)
        draw.rounded_rectangle(body_box, radius=75, fill=gopher_blue, outline=(0, 130, 170, 255), width=4)

        # Ears
        draw.ellipse([(cx - 105, cy - 120), (cx - 70, cy - 85)], fill=gopher_blue, outline=(0, 130, 170, 255), width=3)
        draw.ellipse([(cx + 70, cy - 120), (cx + 105, cy - 85)], fill=gopher_blue, outline=(0, 130, 170, 255), width=3)
        draw.ellipse([(cx - 98, cy - 112), (cx - 78, cy - 92)], fill=(255, 215, 205, 255))
        draw.ellipse([(cx + 78, cy - 112), (cx + 98, cy - 92)], fill=(255, 215, 205, 255))

        # Huge Go Gopher Eyes
        eye_l = (cx - 75, cy - 80, cx - 15, cy - 20)
        eye_r = (cx + 15, cy - 80, cx + 75, cy - 20)
        draw.ellipse(eye_l, fill=(255, 255, 255, 255), outline=(0, 130, 170, 255), width=3)
        draw.ellipse(eye_r, fill=(255, 255, 255, 255), outline=(0, 130, 170, 255), width=3)

        if eye_state == "blink":
            draw.line([(cx - 65, cy - 50), (cx - 25, cy - 50)], fill=(20, 20, 20, 255), width=4)
            draw.line([(cx + 25, cy - 50), (cx + 65, cy - 50)], fill=(20, 20, 20, 255), width=4)
        else:
            # Big dark pupils
            draw.ellipse([(cx - 55, cy - 65), (cx - 30, cy - 35)], fill=(20, 20, 20, 255))
            draw.ellipse([(cx + 30, cy - 65), (cx + 55, cy - 35)], fill=(20, 20, 20, 255))
            draw.ellipse([(cx - 48, cy - 60), (cx - 38, cy - 50)], fill=(255, 255, 255, 255))
            draw.ellipse([(cx + 38, cy - 60), (cx + 48, cy - 50)], fill=(255, 255, 255, 255))

        # Snout / Nose
        draw.ellipse([(cx - 16, cy - 22), (cx + 16, cy + 2)], fill=(40, 30, 30, 255))

        # Buck Teeth
        draw.rectangle([(cx - 12, cy + 8), (cx - 1, cy + 26)], fill=(255, 255, 255, 255), outline=(180, 180, 180, 255), width=1)
        draw.rectangle([(cx + 1, cy + 8), (cx + 12, cy + 26)], fill=(255, 255, 255, 255), outline=(180, 180, 180, 255), width=1)

        # Mouth below teeth
        m_h = int(mouth_open * 14)
        if m_h > 2:
            draw.ellipse([(cx - 14, cy + 22), (cx + 14, cy + 22 + m_h)], fill=(180, 50, 50, 255))

        # Arms
        if pointing:
            draw.ellipse([(cx - 120, cy - 20), (cx - 80, cy + 15)], fill=(255, 215, 205, 255), outline=(0, 130, 170, 255), width=2)
            draw.ellipse([(cx + 70, cy + 30), (cx + 105, cy + 65)], fill=(255, 215, 205, 255), outline=(0, 130, 170, 255), width=2)
        else:
            draw.ellipse([(cx - 85, cy + 30), (cx - 50, cy + 65)], fill=(255, 215, 205, 255), outline=(0, 130, 170, 255), width=2)
            draw.ellipse([(cx + 50, cy + 30), (cx + 85, cy + 65)], fill=(255, 215, 205, 255), outline=(0, 130, 170, 255), width=2)

        return img

    @staticmethod
    def draw_presenter(
        w: int = 400,
        h: int = 500,
        mouth_open: float = 0.0,
        eye_state: str = "normal",
        pointing: bool = True,
        bob_offset: int = 0
    ) -> Image.Image:
        """Draws a stylized Cyberpunk Tech Girl / Host presenter avatar."""
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cx = w // 2
        cy = 150 + bob_offset

        # Futuristic Headset band
        draw.arc([(cx - 80, cy - 90), (cx + 80, cy + 40)], start=170, end=370, fill=(0, 229, 255, 255), width=6)
        # Headset earcups
        draw.rounded_rectangle([(cx - 88, cy - 30), (cx - 72, cy + 30)], radius=6, fill=(168, 85, 247, 255), outline=(0, 229, 255, 255), width=2)
        draw.rounded_rectangle([(cx + 72, cy - 30), (cx + 88, cy + 30)], radius=6, fill=(168, 85, 247, 255), outline=(0, 229, 255, 255), width=2)
        # Microphone boom
        draw.line([(cx - 75, cy + 15), (cx - 35, cy + 40)], fill=(0, 229, 255, 255), width=3)
        draw.ellipse([(cx - 38, cy + 36), (cx - 28, cy + 46)], fill=(0, 255, 180, 255))

        # Face (Skin tone)
        skin_color = (255, 224, 205, 255)
        face_poly = [
            (cx - 65, cy - 40), (cx + 65, cy - 40),
            (cx + 60, cy + 35), (cx, cy + 85), (cx - 60, cy + 35)
        ]
        draw.polygon(face_poly, fill=skin_color, outline=(220, 180, 160, 255))

        # Cyber Hair (Purple / Neon cyan highlights)
        hair_color = (48, 25, 75, 255)
        draw.chord([(cx - 75, cy - 85), (cx + 75, cy + 5)], start=180, end=360, fill=hair_color)
        draw.polygon([(cx - 70, cy - 30), (cx - 40, cy + 20), (cx - 50, cy - 40)], fill=hair_color)
        draw.polygon([(cx + 70, cy - 30), (cx + 40, cy + 20), (cx + 50, cy - 40)], fill=hair_color)

        # Futuristic Visor Glasses
        draw.polygon([(cx - 50, cy - 8), (cx + 50, cy - 8), (cx + 40, cy + 16), (cx - 40, cy + 16)], fill=(0, 229, 255, 200), outline=(255, 255, 255, 255), width=2)

        # Eyes (under visor or visible)
        if eye_state == "blink":
            draw.line([(cx - 35, cy + 4), (cx - 15, cy + 4)], fill=(20, 20, 40, 255), width=2)
            draw.line([(cx + 15, cy + 4), (cx + 35, cy + 4)], fill=(20, 20, 40, 255), width=2)
        else:
            draw.ellipse([(cx - 32, cy - 2), (cx - 18, cy + 10)], fill=(120, 40, 200, 255))
            draw.ellipse([(cx + 18, cy - 2), (cx + 32, cy + 10)], fill=(120, 40, 200, 255))
            draw.ellipse([(cx - 28, cy), (cx - 22, cy + 6)], fill=(255, 255, 255, 255))
            draw.ellipse([(cx + 22, cy), (cx + 28, cy + 6)], fill=(255, 255, 255, 255))

        # Animated Mouth
        m_h = max(3, int(4 + mouth_open * 16))
        my = cy + 48
        draw.rounded_rectangle([(cx - 16, my - m_h // 2), (cx + 16, my + m_h // 2)], radius=m_h // 2, fill=(235, 70, 110, 255))

        # Neck & Cyber Jacket
        draw.rectangle([(cx - 18, cy + 70), (cx + 18, cy + 110)], fill=skin_color)
        # Jacket
        jacket_color = (20, 25, 45, 255)
        jacket_poly = [
            (cx - 20, cy + 95), (cx + 20, cy + 95),
            (cx + 85, cy + 240), (cx - 85, cy + 240)
        ]
        draw.polygon(jacket_poly, fill=jacket_color, outline=(0, 229, 255, 255), width=3)
        # Glowing Collar
        draw.line([(cx - 20, cy + 95), (cx, cy + 140)], fill=(168, 85, 247, 255), width=4)
        draw.line([(cx + 20, cy + 95), (cx, cy + 140)], fill=(168, 85, 247, 255), width=4)

        # Arms
        if pointing:
            draw.line([(cx - 70, cy + 130), (cx - 145, cy + 60)], fill=(20, 25, 45, 255), width=18)
            draw.line([(cx - 70, cy + 130), (cx - 145, cy + 60)], fill=(0, 229, 255, 255), width=4)
            draw.ellipse([(cx - 160, cy + 45), (cx - 130, cy + 75)], fill=skin_color)
            draw.line([(cx + 70, cy + 130), (cx + 110, cy + 210)], fill=(20, 25, 45, 255), width=18)
        else:
            draw.line([(cx - 70, cy + 130), (cx - 110, cy + 210)], fill=(20, 25, 45, 255), width=18)
            draw.line([(cx + 70, cy + 130), (cx + 110, cy + 210)], fill=(20, 25, 45, 255), width=18)

        return img

    @classmethod
    def render_character(
        cls,
        character_type: str,
        w: int = 400,
        h: int = 500,
        mouth_open: float = 0.0,
        eye_state: str = "normal",
        pointing: bool = True,
        bob_offset: int = 0
    ) -> Image.Image:
        c_type = character_type.lower()
        if "ferris" in c_type or "rust" in c_type:
            return cls.draw_ferris(w, h, mouth_open, eye_state, pointing, bob_offset)
        elif "gopher" in c_type or "go" in c_type:
            return cls.draw_gopher(w, h, mouth_open, eye_state, pointing, bob_offset)
        elif "presenter" in c_type or "girl" in c_type or "aria" in c_type or "pallavi" in c_type:
            return cls.draw_presenter(w, h, mouth_open, eye_state, pointing, bob_offset)
        else: # default robot
            return cls.draw_robot(w, h, mouth_open, eye_state, pointing, bob_offset)
