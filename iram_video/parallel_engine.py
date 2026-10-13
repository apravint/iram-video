"""
Asynchronous & Parallel Video Rendering Pipeline for IRAM Video.
Orchestrates concurrent TTS audio synthesis, parallel visual asset generation,
and speculative multi-worker compilation across background thread workers.
"""

import sys
import time
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional, Callable

from .voice import VoiceSynthesizer
from .audio_synth import synthesize_mood_track

logger = logging.getLogger("iram_video.parallel")


class ParallelPipelineEngine:
    """
    Executes screenplay asset generation concurrently:
    1. Fires TTS voiceover synthesis immediately in a background worker.
    2. Concurrently launches parallel visual asset workers (B-roll, Generative, Motion Canvas).
    3. Concurrently synthesizes soundtrack and soundscapes.
    4. Merges synchronized tracks as soon as both audio and visuals settle.
    """

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers

    def execute_parallel_scene_generation(
        self,
        scenes: List[Dict[str, Any]],
        audio_dir: Path,
        voice_synth: VoiceSynthesizer,
        visual_renderer_fn: Callable[[Dict[str, Any], int], Any],
        music_mood: str = "documentary",
        music_duration: float = 30.0,
        music_out_path: Optional[Path] = None,
        progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Executes TTS synthesis and visual synthesis concurrently.
        Returns dictionary with synthesized scenes, visual assets, and music path.
        """
        start_time = time.time()
        total_scenes = len(scenes)

        if progress_callback:
            progress_callback("pipeline_start", {"total_scenes": total_scenes})

        # 1. Fire Voiceover Synthesis Worker
        tts_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="tts_worker")
        tts_future = tts_executor.submit(voice_synth.synthesize, scenes, audio_dir)

        # 2. Fire Background Music Worker (if requested)
        music_future = None
        if music_mood and music_mood != "none" and music_out_path:
            music_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="music_worker")
            music_future = music_executor.submit(
                synthesize_mood_track, music_mood, music_duration, music_out_path
            )

        # 3. Fire Parallel Visual Asset Workers
        visual_results: Dict[int, Any] = {}
        visual_executor = ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="visual_worker")
        visual_futures = {}

        for idx, sc in enumerate(scenes):
            f = visual_executor.submit(visual_renderer_fn, sc, idx)
            visual_futures[f] = idx

        # Await visual asset completion as they finish
        for f in as_completed(visual_futures):
            idx = visual_futures[f]
            try:
                res = f.result()
                visual_results[idx] = res
                if progress_callback:
                    progress_callback("visual_scene_ready", {
                        "scene_index": idx,
                        "total_scenes": total_scenes,
                        "result": res
                    })
            except Exception as e:
                logger.error(f"Visual asset generation failed for scene {idx}: {e}")
                visual_results[idx] = None
                if progress_callback:
                    progress_callback("visual_scene_error", {
                        "scene_index": idx,
                        "error": str(e)
                    })

        visual_executor.shutdown(wait=True)

        # Await TTS synthesis
        try:
            synthesized_scenes = tts_future.result()
            if progress_callback:
                progress_callback("tts_complete", {"scene_count": len(synthesized_scenes)})
        except Exception as e:
            logger.error(f"TTS synthesis worker failed: {e}")
            raise e
        finally:
            tts_executor.shutdown(wait=True)

        # Await Music generation
        music_ready = False
        if music_future:
            try:
                music_future.result()
                music_ready = True
                if progress_callback:
                    progress_callback("music_ready", {"path": str(music_out_path)})
            except Exception as e:
                logger.warning(f"Background music generation failed: {e}")
            finally:
                music_executor.shutdown(wait=True)

        elapsed = time.time() - start_time
        if progress_callback:
            progress_callback("pipeline_complete", {
                "elapsed_seconds": round(elapsed, 2),
                "total_scenes": total_scenes
            })

        return {
            "scenes": synthesized_scenes,
            "visuals": visual_results,
            "music_ready": music_ready,
            "elapsed_seconds": elapsed
        }
