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

    def test_scene_beats_extraction(self):
        from iram_video.b_roll import MediaFetcher
        sample_scene = {
            "narration": "In 2021, the James Webb Space Telescope launched into deep space. It unfolded a massive gold mirror to capture distant infrared light.",
            "duration": 12.0
        }
        beats = MediaFetcher.extract_scene_beats(sample_scene, 12.0)
        self.assertTrue(len(beats) >= 2)
        total_dur = sum(b["duration"] for b in beats)
        self.assertAlmostEqual(total_dur, 12.0, delta=0.1)

    def test_ai_video_engine_fallback_chain(self):
        from iram_video.ai_video import AIVideoEngine
        out_dir = Path("/tmp/test_ai_video_fallback")
        out_dir.mkdir(parents=True, exist_ok=True)
        sample_beat = {
            "query": "solar flare space",
            "phrase": "A colossal solar flare erupts from the sun.",
            "duration": 4.5,
            "ai_prompt": "Cinematic 8k shot of a solar flare erupting into dark space"
        }
        # With veo requested, if quota limit hit or unbilled, it MUST gracefully fallback and return a valid file
        result_file = AIVideoEngine.fetch_or_generate_beat_media(
            sample_beat, out_dir, "test_01", is_shorts=False, provider="veo"
        )
        self.assertTrue(result_file.exists())
        self.assertTrue(result_file.stat().st_size > 1000)

    def test_anchor_phrase_extraction(self):
        from iram_video.b_roll import MediaFetcher
        ta_topic = "சென்னை மெட்ரோ இரண்டாம் கட்ட திட்டம் (Phase 2): 116 கி.மீ தொலைவு | Chennai Metro Phase 2 Launch"
        anchor = MediaFetcher.extract_anchor_phrase(ta_topic)
        self.assertIn("Chennai Metro", anchor)

        en_topic = "Quantum Computing Architecture and Qubits"
        en_anchor = MediaFetcher.extract_anchor_phrase(en_topic)
        self.assertIn("Quantum Computing", en_anchor)

    def test_noise_filtering(self):
        from iram_video.b_roll import MediaFetcher
        # Green fruit Brazilian forest must be flagged as noise
        is_noise_forest = MediaFetcher.is_noise_candidate(
            "File:Corredor Florestal - Pontal do Paranapanema.jpg",
            query="corridor",
            topic="Chennai Metro"
        )
        self.assertTrue(is_noise_forest)

        # Japanese bus with cartoon face must be flagged as noise
        is_noise_bus = MediaFetcher.is_noise_candidate(
            "File:Nagaokakyo Happy Bus.jpg",
            query="feeder",
            topic="Chennai Metro"
        )
        self.assertTrue(is_noise_bus)

        # Authentic Chennai Metro train/feeder must NOT be flagged as noise
        is_noise_metro = MediaFetcher.is_noise_candidate(
            "File:Chennai metro feeder service.jpg",
            query="feeder",
            topic="Chennai Metro"
        )
        self.assertFalse(is_noise_metro)

    def test_duplicate_media_avoidance(self):
        from iram_video.b_roll import MediaFetcher
        MediaFetcher.reset_session()
        self.assertEqual(len(MediaFetcher._used_urls), 0)
        MediaFetcher._used_urls.add("https://example.com/photo1.jpg")
        self.assertIn("https://example.com/photo1.jpg", MediaFetcher._used_urls)
        MediaFetcher.reset_session()
        self.assertEqual(len(MediaFetcher._used_urls), 0)

    def test_voice_synth_duration_guard(self):
        from iram_video.voice import VoiceSynthesizer
        vs = VoiceSynthesizer()
        # Non-existent or empty file should safely return default 3.0 seconds rather than crash
        dur = vs.get_duration(Path("/tmp/non_existent_audio_file.mp3"))
        self.assertAlmostEqual(dur, 3.0)

    def test_thumbnail_generation(self):
        from iram_video.thumbnail import generate_thumbnail
        with tempfile.TemporaryDirectory() as td:
            thumb_out = Path(td) / "test_thumb.png"
            theme = {"bg": [10, 14, 24], "accent": [0, 229, 255], "secondary": [168, 85, 247]}
            generate_thumbnail(
                title="சென்னை மெட்ரோ Phase 2 Launch",
                bullets=["116 km Network", "3 New Corridors", "Driverless Trains"],
                theme=theme,
                output_path=thumb_out,
                is_shorts=False,
                is_cinema=False,
                character="robot"
            )
            self.assertTrue(thumb_out.exists())
            self.assertTrue(thumb_out.stat().st_size > 1000)

    def test_geographic_noise_rejection(self):
        from iram_video.b_roll import MediaFetcher
        # Images from Beijing or Shanghai must be rejected when topic is Chennai/India
        self.assertTrue(MediaFetcher.is_noise_candidate("File:Beijing Subway Line 1 Train.jpg", topic="Chennai Metro"))
        self.assertTrue(MediaFetcher.is_noise_candidate("File:Shanghai Metro Phase 2.jpg", topic="Chennai Metro"))
        self.assertTrue(MediaFetcher.is_noise_candidate("File:Tokyo Minibus.jpg", topic="Chennai Metro"))
        self.assertFalse(MediaFetcher.is_noise_candidate("File:Chennai Metro Phase2 trainset.jpg", topic="Chennai Metro"))

    def test_semantic_beat_classifier(self):
        from iram_video.motion_canvas import classify_semantic_beat

        # Metric phrases
        b_metric = classify_semantic_beat("சென்னை மெட்ரோ இரண்டாம் கட்டம் 116 கி.மீ தொலைவில் 118 நிலையங்களுடன் அமைகிறது.")
        self.assertEqual(b_metric["beat_type"], "metric_card")
        self.assertEqual(b_metric["metric_number"], 116.0)

        # Route / Corridor phrases
        b_route3 = classify_semantic_beat("பாதை 3 மாதவரம் முதல் சிப்காட் வரை அமைகிறது.")
        self.assertEqual(b_route3["beat_type"], "route_map")
        self.assertEqual(len(b_route3["stations"]), 7)

        b_route4 = classify_semantic_beat("Corridor 4 connects Lighthouse to Poonamallee across 26.1 km.")
        self.assertEqual(b_route4["beat_type"], "route_map")

        # General real media phrases
        b_real = classify_semantic_beat("ஓட்டுநர் இல்லாத நவீன ரயில்கள் சென்னை மக்களின் பயணத்தை எளிதாக்கும்.")
        self.assertEqual(b_real["beat_type"], "real_media")

    def test_motion_canvas_rendering(self):
        from iram_video.motion_canvas import MotionCanvas, classify_semantic_beat
        with tempfile.TemporaryDirectory() as td:
            out_metric = Path(td) / "metric.mp4"
            out_route = Path(td) / "route.mp4"

            b_m = classify_semantic_beat("116 கி.மீ மற்றும் 118 நிலையங்கள்")
            MotionCanvas.render_metric_card(b_m, out_metric, duration=1.0)
            self.assertTrue(out_metric.exists())
            self.assertTrue(out_metric.stat().st_size > 1000)

            b_r = classify_semantic_beat("பாதை 3 மாதவரம் முதல் சிப்காட் வரை")
            MotionCanvas.render_route_map(b_r, out_route, duration=1.0)
            self.assertTrue(out_route.exists())
            self.assertTrue(out_route.stat().st_size > 1000)

    def test_sentence_boundary_extraction_from_words(self):
        from iram_video.voice import extract_sentence_boundaries_from_words
        sample_words = [
            {"word": "வணக்கம்.", "start": 0.1, "end": 0.8, "duration": 0.7},
            {"word": "இது", "start": 1.4, "end": 1.7, "duration": 0.3},
            {"word": "மெட்ரோ.", "start": 1.8, "end": 2.4, "duration": 0.6}
        ]
        sentences = extract_sentence_boundaries_from_words(sample_words, "வணக்கம். இது மெட்ரோ.")
        self.assertEqual(len(sentences), 2)
        self.assertEqual(sentences[0]["text"], "வணக்கம்.")
        self.assertEqual(sentences[1]["text"], "இது மெட்ரோ.")
        self.assertAlmostEqual(sentences[0]["start"], 0.1)
        self.assertAlmostEqual(sentences[1]["start"], 1.4)

    def test_sidechain_ducking_filter_syntax(self):
        import subprocess
        fc = (
            "[1:a]volume=0.28[bg];"
            "[bg][0:a]sidechaincompress=threshold=0.08:ratio=5:attack=80:release=380[ducked];"
            "[0:a][ducked]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "sine=frequency=1000:duration=1",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
            "-filter_complex", fc,
            "-map", "[aout]",
            "-f", "null", "-"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)

    def test_smoothstep_zoompan_syntax(self):
        import subprocess
        d = 30
        zp = f"zoompan=z='1.0+0.10*(3*pow(on/{d},2)-2*pow(on/{d},3))':d={d}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=640x360:fps=30"
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "color=c=black:s=640x360:d=1",
            "-vf", zp,
            "-f", "null", "-"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)

if __name__ == "__main__":
    unittest.main()
