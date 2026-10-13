import unittest
import tempfile
import subprocess
from pathlib import Path

from iram_video.templates import VIDEO_TEMPLATES, get_template
from iram_video.color_grade import get_color_grade_filter, COLOR_GRADE_PRESETS
from iram_video.transitions import TransitionEngine
from iram_video.motion_canvas import detect_code_language, MotionCanvas
from iram_video.mcp_server import MCPServer


class TestTemplatesAndTransitions(unittest.TestCase):

    def test_templates_catalog(self):
        """Verify all 7 production templates are registered and complete."""
        expected_templates = [
            "explainer", "tutorial", "listicle", "comparison", "news", "promo", "podcast"
        ]
        for tmpl in expected_templates:
            self.assertIn(tmpl, VIDEO_TEMPLATES)
            spec = get_template(tmpl)
            self.assertIn("name", spec)
            self.assertIn("default_scenes", spec)
            self.assertIn("default_music", spec)
            self.assertIn("default_color_grade", spec)
            self.assertIn("director_directive", spec)
            self.assertIn("directorial_hints", spec)
            self.assertGreater(spec["default_scenes"], 0)

        # Fallback for unknown template defaults gracefully to explainer
        fallback = get_template("non_existent_genre")
        self.assertEqual(fallback["name"], "Deep-Dive Explainer")

    def test_color_grade_presets(self):
        """Verify all color grading presets generate valid FFmpeg filter chains."""
        presets = ["clean", "documentary", "cinematic", "vintage", "noir", "vibrant", "none"]
        for p in presets:
            self.assertIn(p, COLOR_GRADE_PRESETS)
            f_str = get_color_grade_filter(p)
            self.assertIsInstance(f_str, str)
            if p == "none":
                self.assertIn(f_str, ["", "null"])
            elif p == "noir":
                self.assertIn("hue=s=0", f_str)
            elif p == "clean":
                self.assertIn("eq=contrast=1.02", f_str)
            elif p == "cinematic":
                self.assertIn("colorbalance", f_str)

        # Fallback for unknown preset
        self.assertEqual(get_color_grade_filter("invalid_preset"), get_color_grade_filter("clean"))

    def test_multi_language_code_detection(self):
        """Verify dynamic detection of programming languages and filenames."""
        cases = [
            ("Python 3 asyncio web scraper", ("python", "service.py")),
            ("Rust memory safety borrow checker and lifetimes", ("rust", "main.rs")),
            ("Golang goroutines and concurrent channels", ("go", "server.go")),
            ("TypeScript React component state hook", ("typescript", "index.ts")),
            ("PostgreSQL ACID transaction isolation level", ("sql", "query.sql")),
            ("Linux bash shell automation script", ("bash", "deploy.sh")),
            ("C++ low latency high frequency trading engine", ("cpp", "engine.cpp")),
            ("Java Spring Boot microservices REST API", ("java", "EnterpriseService.java")),
        ]
        for prompt, (expected_lang, expected_fname) in cases:
            lang, fname = detect_code_language(prompt)
            self.assertEqual(lang, expected_lang, f"Failed language detection for '{prompt}'")
            self.assertEqual(fname, expected_fname, f"Failed filename detection for '{prompt}'")

    def test_motion_canvas_cards_generation(self):
        """Verify programmatic cards (listicle, step, comparison, code) render valid MP4 files."""
        with tempfile.TemporaryDirectory() as td:
            work_dir = Path(td)

            # 1. Listicle Card
            listicle_mp4 = work_dir / "listicle.mp4"
            beat_listicle = {
                "metric_number": 1,
                "metric_label_en": "Virtual Threads (Project Loom)",
                "phrase": "Lightweight concurrency scaling to millions of active tasks."
            }
            MotionCanvas.render_listicle_card(beat_listicle, listicle_mp4, duration=1.0, is_shorts=False)
            self.assertTrue(listicle_mp4.exists() and listicle_mp4.stat().st_size > 1000)

            # 2. Step Card
            step_mp4 = work_dir / "step.mp4"
            beat_step = {
                "step_number": 2,
                "step_action": "Compile Native Binary via GraalVM",
                "phrase": "Sub-millisecond startup times with zero JIT warmup."
            }
            MotionCanvas.render_step_card(beat_step, step_mp4, duration=1.0, is_shorts=False)
            self.assertTrue(step_mp4.exists() and step_mp4.stat().st_size > 1000)

            # 3. Comparison Card
            comp_mp4 = work_dir / "comparison.mp4"
            beat_comp = {
                "metric_label_en": "Async Event Loop vs Thread-per-Request",
                "phrase": "Throughput comparison benchmark under 100k requests per second."
            }
            MotionCanvas.render_comparison_card(beat_comp, comp_mp4, duration=1.0, is_shorts=False)
            self.assertTrue(comp_mp4.exists() and comp_mp4.stat().st_size > 1000)

            # 4. Code Card for Python
            code_mp4 = work_dir / "code_python.mp4"
            beat_code = {
                "phrase": "FastAPI async endpoints with Pydantic validation.",
                "query": "python async web"
            }
            MotionCanvas.render_code_card(beat_code, code_mp4, duration=1.0, is_shorts=False)
            self.assertTrue(code_mp4.exists() and code_mp4.stat().st_size > 1000)

    def test_transition_engine_xfade_and_fallback(self):
        """Verify TransitionEngine creates xfade transitions with seamless concat fallback."""
        with tempfile.TemporaryDirectory() as td:
            work_dir = Path(td)
            clip1 = work_dir / "c1.mp4"
            clip2 = work_dir / "c2.mp4"
            out_transition = work_dir / "joined_xfade.mp4"

            # Create two 2.0-second test MP4 clips with audio
            for c, color in [(clip1, "black"), (clip2, "blue")]:
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "lavfi", "-i", f"color=c={color}:s=640x360:r=24:d=2.0",
                    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                    "-c:v", "libx264", "-c:a", "aac",
                    "-t", "2.0",
                    str(c)
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Test transition engine join
            TransitionEngine.join_clips_with_transitions(
                [clip1, clip2],
                out_transition,
                transition="fade",
                trans_duration=0.5,
                work_dir=work_dir
            )
            self.assertTrue(out_transition.exists() and out_transition.stat().st_size > 5000)

            # Test single clip fallback (should copy safely)
            single_out = work_dir / "single_out.mp4"
            TransitionEngine.join_clips_with_transitions([clip1], single_out, work_dir=work_dir)
            self.assertTrue(single_out.exists() and single_out.stat().st_size > 1000)

    def test_mcp_server_templates_tool(self):
        """Verify MCP Server exposes list_templates tool and handles execution."""
        server = MCPServer()
        res = server.handle_request({
            "id": "test-1",
            "method": "tools/call",
            "params": {"name": "list_templates", "arguments": {}}
        })
        self.assertIsNotNone(res)
        self.assertIn("result", res)
        content_text = res["result"]["content"][0]["text"]
        self.assertIn("explainer", content_text)
        self.assertIn("tutorial", content_text)
        self.assertIn("listicle", content_text)


if __name__ == "__main__":
    unittest.main()
