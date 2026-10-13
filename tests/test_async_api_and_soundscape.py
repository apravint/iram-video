import os
import time
import unittest
import tempfile
import subprocess
from pathlib import Path
from PIL import Image
from starlette.testclient import TestClient

from iram_video.parallel_engine import ParallelPipelineEngine
from iram_video.state_machine import StateMachineAssetBuilder, AssetRenderState
from iram_video.soundscape_mixer import SoundscapeMixer
from iram_video.avatar import AcceleratedAvatarEngine
from iram_video.character_memory import CharacterVectorMemory
from iram_video.drama import CharacterAnchorRegistry
from iram_video.api import app, task_queue, VideoGenerationRequest


class TestAsyncApiAndSoundscape(unittest.TestCase):

    def test_state_machine_retry_and_fallback(self):
        """Verify managed state machine retries transient failures and cascades through tiers."""
        with tempfile.TemporaryDirectory() as td:
            checkpoint_dir = Path(td)
            builder = StateMachineAssetBuilder(checkpoint_dir, max_retries=2, initial_backoff=0.01)

            asset_id = "test_clip_01"
            out_path = checkpoint_dir / "test_clip_01.mp4"

            attempts_tier1 = 0
            attempts_tier2 = 0

            def failing_tier1():
                nonlocal attempts_tier1
                attempts_tier1 += 1
                raise ConnectionError("Wan 2.2 GPU timeout simulated error")

            def working_tier2():
                nonlocal attempts_tier2
                attempts_tier2 += 1
                # Create small dummy file
                out_path.write_text("dummy video content for testing resilience")
                return out_path

            # Should fail tier1 twice, then cascade to tier2 and succeed
            res = builder.render_asset_with_resilience(
                asset_id,
                out_path,
                tier1_fn=failing_tier1,
                tier2_fn=working_tier2
            )

            self.assertEqual(attempts_tier1, 2)
            self.assertEqual(attempts_tier2, 1)
            self.assertEqual(res, out_path)
            self.assertEqual(builder.state_registry[asset_id]["state"], AssetRenderState.COMPLETED)

            # Test resume: re-running with existing completed file should not execute tier1 or tier2
            attempts_tier1_pre = attempts_tier1
            attempts_tier2_pre = attempts_tier2
            res_resumed = builder.render_asset_with_resilience(
                asset_id,
                out_path,
                tier1_fn=failing_tier1,
                tier2_fn=working_tier2
            )
            self.assertEqual(res_resumed, out_path)
            self.assertEqual(attempts_tier1, attempts_tier1_pre)
            self.assertEqual(attempts_tier2, attempts_tier2_pre)

    def test_soundscape_procedural_generation_and_mix(self):
        """Verify procedural ambient generation (rain, typing, server) and downmixing."""
        with tempfile.TemporaryDirectory() as td:
            work_dir = Path(td)

            p_rain = work_dir / "rain.wav"
            p_typing = work_dir / "typing.wav"
            p_server = work_dir / "server.wav"

            SoundscapeMixer.generate_procedural_ambient("ambient_rain", 1.5, p_rain)
            SoundscapeMixer.generate_procedural_ambient("mechanical_typing", 1.5, p_typing)
            SoundscapeMixer.generate_procedural_ambient("server_room", 1.5, p_server)

            self.assertTrue(p_rain.exists() and p_rain.stat().st_size > 5000)
            self.assertTrue(p_typing.exists() and p_typing.stat().st_size > 5000)
            self.assertTrue(p_server.exists() and p_server.stat().st_size > 5000)

            # Create dummy voice audio
            dummy_voice = work_dir / "voice.wav"
            cmd_voice = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "sine=frequency=440:duration=1.5",
                "-c:a", "pcm_s16le",
                str(dummy_voice)
            ]
            subprocess.run(cmd_voice, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Mix voice with rain soundscape
            mixed_out = work_dir / "mixed_out.wav"
            playlist = [{"type": "ambient_rain", "volume": 0.15}]
            res_mix = SoundscapeMixer.mix_multi_layer_soundscape(
                dummy_voice,
                None,
                playlist,
                mixed_out,
                duration=1.5,
                work_dir=work_dir
            )
            self.assertTrue(mixed_out.exists() and mixed_out.stat().st_size > 1000)

    def test_accelerated_avatar_engine(self):
        """Verify accelerated talking avatar synthesis with rawvideo piping."""
        with tempfile.TemporaryDirectory() as td:
            work_dir = Path(td)

            # Create sample avatar face image
            avatar_img = work_dir / "avatar_face.png"
            img = Image.new("RGBA", (240, 240), (45, 55, 75, 255))
            img.save(avatar_img)

            # Create dummy speech audio
            speech_audio = work_dir / "speech.wav"
            cmd_audio = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "sine=frequency=300:duration=1.0",
                "-c:a", "pcm_s16le",
                str(speech_audio)
            ]
            subprocess.run(cmd_audio, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            avatar_video = work_dir / "avatar_clip.mp4"
            AcceleratedAvatarEngine.create_talking_avatar_video(
                avatar_img,
                speech_audio,
                avatar_video,
                duration=1.0,
                width=240,
                height=240,
                fps=20
            )

            self.assertTrue(avatar_video.exists() and avatar_video.stat().st_size > 2000)

    def test_character_vector_memory(self):
        """Verify character consistency vector storage and similarity retrieval."""
        with tempfile.TemporaryDirectory() as td:
            storage_dir = Path(td)
            mem = CharacterVectorMemory(storage_dir=storage_dir)

            # Store character
            point_id = mem.store_character_anchor(
                character_name="Nova",
                wardrobe="Midnight blue technical suit with gold lapel pin",
                facial_features="Auburn hair, hazel eyes, sharp confident gaze",
                style_signature="Nova architect, midnight blue technical suit",
                episode=1,
                seed=4242
            )
            self.assertIsNotNone(point_id)

            # Retrieve consistent anchor
            anchor = mem.find_consistent_anchor(
                character_name="Nova",
                wardrobe_query="blue suit"
            )
            self.assertIsNotNone(anchor)
            self.assertEqual(anchor["character_name"], "Nova")
            self.assertIn("technical suit", anchor["wardrobe"])

            # Test CharacterAnchorRegistry integration
            registry = CharacterAnchorRegistry(memory=mem)
            prompt_token = registry.get_prompt_anchor("Nova")
            self.assertIn("technical suit", prompt_token)

    def test_fastapi_rest_api_endpoints(self):
        """Verify decoupled FastAPI endpoints and task tracking."""
        client = TestClient(app)

        # Health endpoint
        res_h = client.get("/api/v2/health")
        self.assertEqual(res_h.status_code, 200)
        self.assertEqual(res_h.json()["status"], "healthy")

        # Templates endpoint
        res_t = client.get("/api/v2/templates")
        self.assertEqual(res_t.status_code, 200)
        data_t = res_t.json()
        self.assertTrue(len(data_t) >= 7)

        # Task submission
        payload = {
            "prompt": "Next-Gen Quantum Computing breakthroughs and cryptographic protocols",
            "template": "explainer",
            "aspect_ratio": "16:9",
            "mode": "real"
        }
        res_gen = client.post("/api/v2/generate", json=payload)
        self.assertEqual(res_gen.status_code, 200)
        data_gen = res_gen.json()
        self.assertEqual(data_gen["status"], "queued")
        task_id = data_gen["task_id"]
        self.assertTrue(task_id.startswith("iram_task_"))

        # Task status check
        res_status = client.get(f"/api/v2/tasks/{task_id}")
        self.assertEqual(res_status.status_code, 200)
        data_status = res_status.json()
        self.assertIn(data_status["status"], ["queued", "directing", "rendering_visuals", "completed"])

        # Task listing
        res_list = client.get("/api/v2/tasks")
        self.assertEqual(res_list.status_code, 200)
        self.assertTrue(len(res_list.json()) >= 1)


if __name__ == "__main__":
    unittest.main()
