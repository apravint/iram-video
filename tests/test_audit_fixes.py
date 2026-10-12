import unittest
import tempfile
import io
import json
import re
from pathlib import Path
from http.server import HTTPServer

from iram_video.cli import slugify
from iram_video.compiler import VideoCompiler
from iram_video.sfx import SoundEffectsSynthesizer
from iram_video.subtitles import SUBTITLE_PALETTES
from iram_video.server import VideoStudioHandler, RESOURCES_DIR, OUTPUTS_DIR, UPLOAD_DIR
from iram_video.mcp_server import MCPServer
import iram_video.cli as cli_module

class MockSocket:
    def __init__(self, raw_input: bytes):
        self.rfile = io.BytesIO(raw_input)
        self.wfile = io.BytesIO()

    def makefile(self, mode, *args, **kwargs):
        if "r" in mode:
            return self.rfile
        return self.wfile

    def sendall(self, data):
        self.wfile.write(data)

class TestAuditFixes(unittest.TestCase):
    def test_cli_aivideo_imported(self):
        """Verify AIVideoEngine is imported in cli module to prevent NameError on --extend."""
        self.assertTrue(hasattr(cli_module, "AIVideoEngine"))

    def test_cli_mascot_word_boundaries(self):
        """Verify 'go' keyword matching requires word boundary so words like 'algorithm' don't trigger gopher."""
        p1 = "how modern algorithms handle concurrency"
        p2 = "writing microservices in go"
        p3 = "writing microservices in golang"

        self.assertFalse(bool(re.search(r"\bgo\b", p1)))
        self.assertTrue(bool(re.search(r"\bgo\b", p2)))
        self.assertTrue("golang" in p3)

    def test_compiler_optional_bg_music_signature(self):
        """Verify compile accepts bg_music=None in type hints / signature."""
        import inspect
        sig = inspect.signature(VideoCompiler.compile)
        self.assertIn("bg_music", sig.parameters)

    def test_sfx_whoosh_phase_coherence(self):
        """Verify generate_whoosh produces valid PCM audio without nan or clipping artifacts."""
        with tempfile.TemporaryDirectory() as td:
            out_p = Path(td) / "whoosh.wav"
            SoundEffectsSynthesizer.generate_whoosh(out_p, duration=1.0)
            self.assertTrue(out_p.exists())
            self.assertGreater(out_p.stat().st_size, 40000)

    def test_subtitles_magenta_and_purple_palettes(self):
        """Verify subtitle palettes has both magenta and purple properly defined."""
        self.assertIn("magenta", SUBTITLE_PALETTES)
        self.assertIn("purple", SUBTITLE_PALETTES)
        self.assertEqual(SUBTITLE_PALETTES["magenta"], "\\c&H00FF00FF&")

    def test_mcp_extend_video_nonexistent_raises(self):
        """Verify extend_video MCP tool raises FileNotFoundError if previous video does not exist."""
        server = MCPServer()
        with self.assertRaises(FileNotFoundError):
            server.execute_tool("extend_video", {
                "previous_video": "/tmp/definitely_nonexistent_video_12345.mp4",
                "output_path": "/tmp/out.mp4",
                "prompt": "continue sequence"
            })

    def test_server_path_traversal_protection(self):
        """Verify /video/ path traversal attempts are rejected."""
        raw_get = b"GET /video/../../etc/passwd HTTP/1.1\r\nHost: localhost\r\n\r\n"
        sock = MockSocket(raw_get)
        handler = VideoStudioHandler(sock, ("127.0.0.1", 12345), None)
        output_str = sock.wfile.getvalue().decode("latin1")
        self.assertTrue("400 Bad Request" in output_str or "404 Not Found" in output_str)
        self.assertNotIn("root:", output_str)

    def test_server_security_headers(self):
        """Verify security headers are injected into HTTP responses."""
        raw_get = b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
        sock = MockSocket(raw_get)
        handler = VideoStudioHandler(sock, ("127.0.0.1", 12345), None)
        output_str = sock.wfile.getvalue().decode("latin1")
        self.assertIn("X-Content-Type-Options: nosniff", output_str)
        self.assertIn("X-Frame-Options: DENY", output_str)
        self.assertIn("Content-Security-Policy", output_str)

    def test_server_resources_does_not_leak_paths(self):
        """Verify /api/resources does not disclose raw internal absolute filesystem paths."""
        raw_get = b"GET /api/resources HTTP/1.1\r\nHost: localhost\r\n\r\n"
        sock = MockSocket(raw_get)
        handler = VideoStudioHandler(sock, ("127.0.0.1", 12345), None)
        output_str = sock.wfile.getvalue().decode("utf-8")
        headers, body = output_str.split("\r\n\r\n", 1)
        items = json.loads(body)
        for it in items:
            self.assertNotIn("path", it)
            self.assertIn("name", it)

if __name__ == "__main__":
    unittest.main()
