"""
Unit tests for best logics ported from itsPremkumar/Automated-Video-Generator:
1. Multi-source zero-cost stock media (Openverse, Coverr, NASA, Met Museum, and Media Verifier)
2. Procedural FFmpeg audio SFX (Ding, Click, Pop, Notification, Swish, Transition, Bounce, Riser)
3. Smart voice pacing, silence trimming, and voice effects (Deep, Robot, Telephone, etc.)
4. Kinetic subtitle syllable-weighted timing heuristic, FFmpeg drawtext escaping, and SRT/VTT export
5. Dynamic audio sidechain compression BGM ducking
6. AutoCut scene detection and rhythmic video assembly
"""

import os
import shutil
import tempfile
import unittest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image

from iram_video.b_roll import MediaFetcher
from iram_video.sfx import SoundEffectsSynthesizer
from iram_video.voice import VoiceSynthesizer
from iram_video.subtitles import (
    count_syllables,
    syllable_word_timings,
    ffmpeg_drawtext_escape,
    export_srt,
    export_vtt,
    KineticSubtitleGenerator
)
from iram_video.soundscape_mixer import SoundscapeMixer
from iram_video.autocut import detect_scenes, smart_assemble


class TestAutomatedVideoGeneratorLogics(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="iram_avg_test_"))

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    # ─── 1. Zero-Cost Stock Media Providers & Verifier ──────────────────

    def test_search_openverse_mock(self):
        mock_data = {
            "results": [
                {
                    "url": "https://example.com/openverse_img.jpg",
                    "width": 1920,
                    "height": 1080,
                    "title": "Clean Energy Wind Turbine",
                    "license": "CC0"
                }
            ]
        }
        with patch("urllib.request.urlopen") as mock_url:
            mock_resp = MagicMock()
            mock_resp.read.return_value = str(mock_data).replace("'", '"').encode("utf-8")
            mock_resp.__enter__.return_value = mock_resp
            mock_url.return_value = mock_resp

            results = MediaFetcher.search_openverse("wind turbine", require_video=False)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["provider"], "openverse")
            self.assertEqual(results[0]["url"], "https://example.com/openverse_img.jpg")

    def test_search_coverr_mock(self):
        mock_data = {
            "videos": [
                {
                    "url": "https://storage.coverr.co/videos/nature_drone.mp4",
                    "title": "Drone Forest View",
                    "width": 1920,
                    "height": 1080
                }
            ]
        }
        with patch("urllib.request.urlopen") as mock_url:
            mock_resp = MagicMock()
            mock_resp.read.return_value = str(mock_data).replace("'", '"').encode("utf-8")
            mock_resp.__enter__.return_value = mock_resp
            mock_url.return_value = mock_resp

            results = MediaFetcher.search_coverr("nature")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["provider"], "coverr")
            self.assertEqual(results[0]["type"], "video")

    def test_verify_media_file_valid_and_invalid(self):
        # 1. Non-existent file
        self.assertFalse(MediaFetcher.verify_media_file(self.test_dir / "ghost.jpg"))

        # 2. Corrupt / tiny file (<4000 bytes)
        tiny_file = self.test_dir / "tiny.jpg"
        tiny_file.write_bytes(b"not an image")
        self.assertFalse(MediaFetcher.verify_media_file(tiny_file))

        # 3. Valid large PIL image
        valid_img_path = self.test_dir / "valid.jpg"
        img = Image.new("RGB", (640, 480), color=(30, 41, 59))
        img.save(valid_img_path, format="JPEG", quality=95)
        # Verify file size > 4000 bytes
        if valid_img_path.stat().st_size >= 4000:
            self.assertTrue(MediaFetcher.verify_media_file(valid_img_path))

    # ─── 2. Procedural Audio SFX Engine ─────────────────────────────────

    def test_procedural_sfx_generators(self):
        ding_path = self.test_dir / "ding.wav"
        SoundEffectsSynthesizer.generate_ding(ding_path, duration=0.2)
        self.assertTrue(ding_path.exists())
        self.assertGreater(ding_path.stat().st_size, 500)

        click_path = self.test_dir / "click.wav"
        SoundEffectsSynthesizer.generate_click(click_path, duration=0.05)
        self.assertTrue(click_path.exists())
        self.assertGreater(click_path.stat().st_size, 200)

        pop_path = self.test_dir / "pop.wav"
        SoundEffectsSynthesizer.generate_pop(pop_path, duration=0.08)
        self.assertTrue(pop_path.exists())
        self.assertGreater(pop_path.stat().st_size, 200)

        notif_path = self.test_dir / "notif.wav"
        SoundEffectsSynthesizer.generate_notification(notif_path, duration=0.2)
        self.assertTrue(notif_path.exists())
        self.assertGreater(notif_path.stat().st_size, 500)

        swish_path = self.test_dir / "swish.wav"
        SoundEffectsSynthesizer.generate_swish(swish_path, duration=0.15)
        self.assertTrue(swish_path.exists())

        riser_path = self.test_dir / "riser.wav"
        SoundEffectsSynthesizer.generate_riser(riser_path, duration=0.5)
        self.assertTrue(riser_path.exists())

    def test_universal_sfx_dispatcher(self):
        out_path = self.test_dir / "bounce_test.wav"
        res = SoundEffectsSynthesizer.generate_sfx("bounce", out_path, duration=0.3)
        self.assertEqual(res, out_path)
        self.assertTrue(out_path.exists())

    # ─── 3. Voice Effects & Silence Trimming ─────────────────────────────

    def test_estimate_audio_duration(self):
        text = "Java and Spring Boot framework architecture with reactive endpoints"
        est = VoiceSynthesizer.estimate_audio_duration(text, wpm=150.0)
        self.assertGreaterEqual(est, 2.5)

    def test_apply_voice_effect_robot(self):
        # Create a raw wave test file
        src_wav = self.test_dir / "speech_sample.wav"
        SoundEffectsSynthesizer.generate_telemetry(src_wav, duration=0.6)

        fx_out = self.test_dir / "speech_robot.wav"
        res = VoiceSynthesizer.apply_voice_effect(src_wav, effect="robot", out_path=fx_out)
        self.assertTrue(res.exists())
        self.assertGreater(res.stat().st_size, 500)

    def test_trim_silence_graceful_pass(self):
        src_wav = self.test_dir / "sample_tone.wav"
        SoundEffectsSynthesizer.generate_ding(src_wav, duration=0.4)
        trimmed = VoiceSynthesizer.trim_silence(src_wav)
        self.assertTrue(trimmed.exists())

    # ─── 4. Subtitle Syllable Timings & Sidecar Serialization ───────────

    def test_count_syllables(self):
        self.assertEqual(count_syllables("cloud"), 1)
        self.assertEqual(count_syllables("architecture"), 4)
        self.assertEqual(count_syllables("microservices"), 5)

    def test_syllable_word_timings_normalized(self):
        phrase = "Enterprise microservices with high scalability and fault tolerance"
        duration = 4.2
        timings = syllable_word_timings(phrase, duration)
        self.assertEqual(len(timings), len(phrase.split()))
        self.assertEqual(timings[0]["start"], 0.0)
        self.assertEqual(timings[-1]["end"], duration)

        # Monotonically increasing timestamps
        for i in range(len(timings) - 1):
            self.assertLessEqual(timings[i]["start"], timings[i + 1]["start"])
            self.assertLessEqual(timings[i]["end"], timings[i + 1]["end"])

    def test_ffmpeg_drawtext_escape(self):
        unsafe = "It's a high:speed, \"mission-critical\" \\system!"
        escaped = ffmpeg_drawtext_escape(unsafe)
        # Apostrophe replaced with typographic quote ’
        self.assertNotIn("'", escaped)
        self.assertIn("’", escaped)
        # Colons escaped
        self.assertIn("\\:", escaped)
        # Quotes escaped
        self.assertIn('\\"', escaped)
        # Commas escaped
        self.assertIn("\\,", escaped)

    def test_export_srt_and_vtt(self):
        scenes = [
            {"narration": "Welcome to Java and Spring Boot mastery.", "duration": 3.0},
            {"narration": "Build high throughput reactive microservices.", "duration": 4.5}
        ]
        srt_file = self.test_dir / "subtitles.srt"
        vtt_file = self.test_dir / "subtitles.vtt"

        export_srt(scenes, srt_file)
        self.assertTrue(srt_file.exists())
        content_srt = srt_file.read_text(encoding="utf-8")
        self.assertIn("00:00:00,000 --> 00:00:03,000", content_srt)
        self.assertIn("Welcome to Java", content_srt)

        export_vtt(scenes, vtt_file)
        self.assertTrue(vtt_file.exists())
        content_vtt = vtt_file.read_text(encoding="utf-8")
        self.assertTrue(content_vtt.startswith("WEBVTT"))
        self.assertIn("00:00:00.000 --> 00:00:03.000", content_vtt)

    # ─── 5. Audio Sidechain Compression Ducking ─────────────────────────

    def test_mix_multi_layer_soundscape_with_sidechain(self):
        voice_wav = self.test_dir / "voice.wav"
        bgm_wav = self.test_dir / "bgm.wav"
        out_wav = self.test_dir / "mixed_soundscape.wav"

        SoundEffectsSynthesizer.generate_whoosh(voice_wav, duration=2.0)
        SoundEffectsSynthesizer.generate_ding(bgm_wav, duration=2.0)

        playlist = [{"type": "room_tone"}]
        res = SoundscapeMixer.mix_multi_layer_soundscape(
            narration_wav=voice_wav,
            bg_music_wav=bgm_wav,
            soundscape_playlist=playlist,
            output_wav=out_wav,
            duration=2.0,
            use_sidechain=True
        )
        self.assertTrue(res.exists())
        self.assertGreater(res.stat().st_size, 1000)

    # ─── 6. AutoCut Scene Detection & Assembly ──────────────────────────

    def test_autocut_detect_and_assemble(self):
        # Generate a synthetic 3-second test video clip with color bars
        test_video = self.test_dir / "test_input.mp4"
        import subprocess
        make_cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=duration=3:size=320x240:rate=10",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(test_video)
        ]
        subprocess.run(make_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 1. Test detect_scenes
        scenes = detect_scenes(test_video, sensitivity=0.3)
        self.assertIsInstance(scenes, list)
        self.assertGreaterEqual(len(scenes), 1)

        # 2. Test smart_assemble
        assembled_video = self.test_dir / "test_assembled.mp4"
        out_res = smart_assemble(test_video, target_duration=2.0, out_path=assembled_video)
        self.assertTrue(out_res.exists())
        self.assertGreater(out_res.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
