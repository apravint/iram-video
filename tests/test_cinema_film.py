import unittest
import tempfile
from pathlib import Path
from PIL import Image

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

if __name__ == "__main__":
    unittest.main()
