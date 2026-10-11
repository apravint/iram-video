import os
import time
import json
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, Any, List

from .b_roll import MediaFetcher

class AIVideoEngine:
    """
    Multi-Tier AI Video Generation Engine with Cascading Fallback:
    Tier 1: Google Veo 3.1 / 2.0 (Gemini API & Vertex AI)
    Tier 2: Fal.ai (Wan 2.1, Kling 1.5, Luma Ray 2)
    Tier 3: Replicate (Wan 2.1, Minimax Hailuo Video-01)
    Tier 4: Public Domain Media Archives (Wikimedia Commons & NASA 4K/8K Video/Photos)
    Tier 5: Documentary Motion Canvas (Ken Burns Dynamic Push/Pull/Pan)
    """

    _veo_quota_exhausted: bool = False

    @classmethod
    def generate_with_google_veo(
        cls,
        prompt: str,
        out_path: Path,
        duration: float = 5.0,
        is_shorts: bool = False
    ) -> Optional[Path]:
        """Attempts video generation using Google Veo (veo-3.1-generate-preview / veo-2.0-generate-001)."""
        if cls._veo_quota_exhausted:
            return None

        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None

        try:
            from google import genai
            from google.genai import types

            client = genai.Client()
            # Google Veo accepts discrete durations: 4, 6, or 8 seconds
            dur_int = 4 if duration <= 5.0 else (6 if duration <= 7.0 else 8)
            aspect_ratio = "9:16" if is_shorts else "16:9"

            models_to_try = [
                "veo-3.1-lite-generate-preview",
                "veo-3.1-fast-generate-preview",
                "veo-3.1-generate-preview",
                "veo-2.0-generate-001"
            ]

            cinematic_prompt = (
                f"Cinematic photorealistic 8k footage: {prompt}. "
                "Natural lighting, continuous camera motion, 35mm lens, master documentary capture, high visual detail."
            )

            for model_name in models_to_try:
                try:
                    print(f"   ⚡ [Google Veo] Synthesizing video with '{model_name}' ({dur_int}s)...")
                    operation = client.models.generate_videos(
                        model=model_name,
                        source=types.GenerateVideosSource(prompt=cinematic_prompt),
                        config=types.GenerateVideosConfig(
                            aspect_ratio=aspect_ratio,
                            duration_seconds=dur_int
                        )
                    )

                    # Poll operation with timeout (max 90 seconds)
                    start_t = time.time()
                    while not operation.done:
                        if time.time() - start_t > 90:
                            print(f"   ⚠️ [Google Veo] Operation timed out after 90s on {model_name}")
                            break
                        time.sleep(5)
                        operation = client.operations.get(operation)

                    if operation.done and operation.result and operation.result.generated_videos:
                        gen_video = operation.result.generated_videos[0]
                        gen_video.video.save(str(out_path))
                        if out_path.exists() and out_path.stat().st_size > 10000:
                            print(f"   ✓ [Google Veo] Successfully synthesized AI video: {out_path.name}")
                            return out_path
                except Exception as sub_err:
                    err_msg = str(sub_err)
                    if "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg:
                        cls._veo_quota_exhausted = True
                        print(f"   ⚠️ [Google Veo Notice] Quota limit reached (429 RESOURCE_EXHAUSTED)")
                        break
                    elif "404" in err_msg or "NOT_FOUND" in err_msg:
                        continue
                    else:
                        cls._veo_quota_exhausted = True
                        print(f"   ⚠️ [Google Veo Notice] {err_msg[:90]}")
                        break
        except Exception as e:
            print(f"   ⚠️ [Google Veo Init] {e}")
        return None

    @classmethod
    def generate_with_fal(
        cls,
        prompt: str,
        out_path: Path,
        duration: float = 5.0,
        is_shorts: bool = False
    ) -> Optional[Path]:
        """Attempts video generation using Fal.ai (Wan 2.1 / Kling / Luma)."""
        fal_key = os.getenv("FAL_KEY") or os.getenv("FAL_API_KEY")
        if not fal_key:
            return None

        try:
            import requests

            endpoint = "https://queue.fal.run/fal-ai/wan/v2.1/text-to-video"
            aspect_ratio = "9:16" if is_shorts else "16:9"
            payload = {
                "prompt": f"Cinematic photorealistic documentary shot: {prompt}, 4k ultra detailed",
                "aspect_ratio": aspect_ratio
            }
            headers = {
                "Authorization": f"Key {fal_key}",
                "Content-Type": "application/json"
            }

            print("   ⚡ [Fal.ai Wan 2.1] Submitting request...")
            resp = requests.post(endpoint, json=payload, headers=headers, timeout=15)
            if resp.status_code not in (200, 201, 202):
                print(f"   ⚠️ [Fal.ai Notice] Status {resp.status_code}: {resp.text[:80]}")
                return None

            data = resp.json()
            status_url = data.get("status_url")
            response_url = data.get("response_url")

            # Poll for completion
            start_t = time.time()
            while time.time() - start_t < 90:
                time.sleep(5)
                check = requests.get(status_url or response_url, headers=headers, timeout=10)
                if check.status_code == 200:
                    cdata = check.json()
                    status = cdata.get("status")
                    if status == "COMPLETED" or "video" in cdata:
                        video_url = cdata.get("video", {}).get("url") or cdata.get("output", {}).get("video", {}).get("url")
                        if video_url:
                            v_resp = requests.get(video_url, timeout=30)
                            if v_resp.status_code == 200:
                                with open(out_path, "wb") as f:
                                    f.write(v_resp.content)
                                print(f"   ✓ [Fal.ai Wan 2.1] Successfully generated video: {out_path.name}")
                                return out_path
                    elif status in ("FAILED", "CANCELLED"):
                        print(f"   ⚠️ [Fal.ai Notice] Job status {status}")
                        return None
        except Exception as e:
            print(f"   ⚠️ [Fal.ai Error] {e}")
        return None

    @classmethod
    def generate_with_replicate(
        cls,
        prompt: str,
        out_path: Path,
        duration: float = 5.0,
        is_shorts: bool = False
    ) -> Optional[Path]:
        """Attempts video generation using Replicate (Wan 2.1 / Minimax Hailuo)."""
        replicate_token = os.getenv("REPLICATE_API_TOKEN") or os.getenv("REPLICATE_API_KEY")
        if not replicate_token:
            return None

        try:
            import requests

            endpoint = "https://api.replicate.com/v1/models/wan-video/wan-2.1-14b/predictions"
            aspect_ratio = "9:16" if is_shorts else "16:9"
            payload = {
                "input": {
                    "prompt": f"Cinematic documentary shot: {prompt}, 8k photorealistic",
                    "aspect_ratio": aspect_ratio
                }
            }
            headers = {
                "Authorization": f"Bearer {replicate_token}",
                "Content-Type": "application/json"
            }

            print("   ⚡ [Replicate Wan 2.1] Submitting request...")
            resp = requests.post(endpoint, json=payload, headers=headers, timeout=15)
            if resp.status_code not in (200, 201):
                print(f"   ⚠️ [Replicate Notice] Status {resp.status_code}: {resp.text[:80]}")
                return None

            data = resp.json()
            poll_url = data.get("urls", {}).get("get")
            if not poll_url:
                return None

            start_t = time.time()
            while time.time() - start_t < 90:
                time.sleep(5)
                check = requests.get(poll_url, headers=headers, timeout=10)
                if check.status_code == 200:
                    cdata = check.json()
                    status = cdata.get("status")
                    if status == "succeeded":
                        output = cdata.get("output")
                        video_url = output if isinstance(output, str) else (output[0] if isinstance(output, list) else None)
                        if video_url:
                            v_resp = requests.get(video_url, timeout=30)
                            if v_resp.status_code == 200:
                                with open(out_path, "wb") as f:
                                    f.write(v_resp.content)
                                print(f"   ✓ [Replicate Wan 2.1] Successfully generated video: {out_path.name}")
                                return out_path
                    elif status in ("failed", "canceled"):
                        print(f"   ⚠️ [Replicate Notice] Job status {status}")
                        return None
        except Exception as e:
            print(f"   ⚠️ [Replicate Error] {e}")
        return None

    @classmethod
    def fetch_or_generate_beat_media(
        cls,
        beat: Dict[str, Any],
        out_dir: Path,
        beat_id: str,
        is_shorts: bool = False,
        provider: str = "auto"
    ) -> Path:
        """
        Main routing function that executes the multi-tier cascading fallback:
        Google Veo -> Fal.ai -> Replicate -> Wikimedia/NASA Stock Archives -> Motion Canvas
        """
        out_dir.mkdir(parents=True, exist_ok=True)
        query = beat.get("query") or beat.get("search_query") or "documentary scene"
        phrase = beat.get("phrase") or beat.get("narration") or query
        duration = float(beat.get("duration", 5.0))
        ai_prompt = beat.get("ai_prompt") or f"{query}. {phrase}"

        target_mp4 = out_dir / f"beat_{beat_id}_ai.mp4"

        # Check cached AI video
        if target_mp4.exists() and target_mp4.stat().st_size > 10000:
            return target_mp4

        prov = provider.lower().strip()

        # Tier 1: Google Veo
        if prov in ("auto", "veo", "google"):
            res = cls.generate_with_google_veo(ai_prompt, target_mp4, duration, is_shorts)
            if res:
                return res
            if prov in ("veo", "google"):
                print("   🔄 [Veo fallback] Falling back to secondary providers...")

        # Tier 2: Fal.ai Wan 2.1 / Kling / Luma
        if prov in ("auto", "fal", "wan", "kling"):
            res = cls.generate_with_fal(ai_prompt, target_mp4, duration, is_shorts)
            if res:
                return res

        # Tier 3: Replicate Wan 2.1 / Minimax
        if prov in ("auto", "replicate"):
            res = cls.generate_with_replicate(ai_prompt, target_mp4, duration, is_shorts)
            if res:
                return res

        # Tier 4: Public Domain Stock Archives (Wikimedia Commons & NASA HD Video/Photos)
        stock_path = MediaFetcher.fetch_media_for_beat(query, out_dir, beat_id)
        if stock_path.exists() and stock_path.stat().st_size > 5000:
            return stock_path

        # Tier 5: Documentary Motion Canvas Fallback
        fallback_img = out_dir / f"beat_{beat_id}.jpg"
        if not fallback_img.exists():
            MediaFetcher.create_clean_documentary_frame(query, fallback_img)
        return fallback_img
