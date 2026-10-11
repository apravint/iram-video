import unittest
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw

from iram_video.renderer import is_tamil_text, split_runs, get_fonts, get_mixed_width, draw_mixed_line
from iram_video.characters import CharacterRenderer
from iram_video.environments import EnvironmentRenderer
from iram_video.sfx import SoundEffectsSynthesizer

class TestCinemaFilmEngine(unittest.TestCase):
    def test_tamil_detection_and_runs(self):
        ta_sample = "தமிழ் மற்றும் English கலவை"
        self.assertTrue(is_tamil_text(ta_sample))
        runs = split_runs(ta_sample)
        self.assertTrue(len(runs) >= 3)
        # Check first run is Tamil
        self.assertTrue(runs[0][1])

    def test_character_rendering(self):
        chars = ["robot", "presenter", "ferris", "gopher"]
        for c in chars:
            img = CharacterRenderer.render_character(c, w=300, h=400, mouth_open=0.5, eye_state="blink", pointing=True)
            self.assertIsInstance(img, Image.Image)
            self.assertEqual(img.size, (300, 400))

    def test_environment_rendering(self):
        sets = ["cyberpunk_city", "quantum_lab", "deep_space", "digital_matrix"]
        for s in sets:
            img = EnvironmentRenderer.render_set(s, w=640, h=360)
            self.assertIsInstance(img, Image.Image)
            self.assertEqual(img.size, (640, 360))

    def test_sfx_synthesis(self):
        with tempfile.TemporaryDirectory() as td:
            p_impact = Path(td) / "impact.wav"
            p_whoosh = Path(td) / "whoosh.wav"
            p_tele = Path(td) / "telemetry.wav"

            SoundEffectsSynthesizer.generate_impact(p_impact, duration=0.5)
            SoundEffectsSynthesizer.generate_whoosh(p_whoosh, duration=0.5)
            SoundEffectsSynthesizer.generate_telemetry(p_tele, duration=0.5)

            self.assertTrue(p_impact.exists() and p_impact.stat().st_size > 1000)
            self.assertTrue(p_whoosh.exists() and p_whoosh.stat().st_size > 1000)
            self.assertTrue(p_tele.exists() and p_tele.stat().st_size > 1000)

    def test_kinetic_subtitles(self):
        from iram_video.subtitles import KineticSubtitleGenerator
        with tempfile.TemporaryDirectory() as td:
            ass_out = Path(td) / "test.ass"
            scenes = [
                {"narration": "Artificial intelligence is expanding into cinematic storytelling", "duration": 4.0},
                {"narration": "தானியங்கி மென்பொருள் மற்றும் கணினி பார்வை", "duration": 3.5}
            ]
            KineticSubtitleGenerator.generate_ass(scenes, ass_out, is_shorts=True, language="ta")
            self.assertTrue(ass_out.exists())
            content = ass_out.read_text(encoding="utf-8")
            self.assertIn("[Script Info]", content)
            self.assertIn("Dialogue: 0,", content)
            self.assertIn("Noto Sans Tamil", content)

    def test_json_ingestion(self):
        from iram_video.cli import load_prompt_from_json
        sample_json = Path("/home/apravint/resources/video-creator-stacks.json")
        if sample_json.exists():
            prompt, style = load_prompt_from_json(sample_json)
            self.assertIn("Video Creator Projects", prompt)
            self.assertTrue(len(prompt) > 20)

    def test_emoji_mixed_typography(self):
        img = Image.new("RGBA", (500, 100), (0, 0, 0, 255))
        draw = ImageDraw.Draw(img)
        fta, fen = get_fonts(24)
        sample = "🎬 AI சினிமா & Code 🚀 🔥"
        w = get_mixed_width(sample, fta, fen, draw)
        self.assertTrue(w > 100)
        end_x = draw_mixed_line(draw, 10, 10, sample, (255, 255, 255), fta, fen)
        self.assertTrue(end_x > 100)

if __name__ == "__main__":
    unittest.main()
