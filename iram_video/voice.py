import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import edge_tts

VOICE_MAP = {
    # English Voices
    "aria": "en-US-AriaNeural",            # Female English: Confident, clear (Default EN)
    "jenny": "en-US-JennyNeural",          # Female English: Friendly
    "emma": "en-US-EmmaNeural",            # Female English: Cheerful
    "christopher": "en-US-ChristopherNeural", # Male English: Authoritative tech
    "guy": "en-US-GuyNeural",              # Male English: Energetic
    "brian": "en-US-BrianNeural",          # Male English: Casual
    "eric": "en-US-EricNeural",            # Male English: Rational

    # Tamil Voices (தமிழ்)
    "pallavi": "ta-IN-PallaviNeural",      # Female Tamil: Friendly, positive (Default TA)
    "valluvar": "ta-IN-ValluvarNeural",    # Male Tamil: Friendly, authoritative
    "tamil-female": "ta-IN-PallaviNeural",
    "tamil-male": "ta-IN-ValluvarNeural"
}


def extract_sentence_boundaries_from_words(word_timings: List[Dict[str, Any]], full_text: str) -> List[Dict[str, Any]]:
    """Groups millisecond word boundary events into coherent sentence beats with exact start/end durations."""
    if not word_timings:
        return []
    sentences = []
    curr_words = []
    for i, wt in enumerate(word_timings):
        curr_words.append(wt)
        is_last = (i == len(word_timings) - 1)
        w_text = wt["word"]
        has_punct = any(w_text.endswith(p) for p in [".", "!", "?", ";", "|", ":"])
        has_pause = False
        if not is_last:
            next_start = word_timings[i + 1]["start"]
            if next_start - wt["end"] >= 0.38:
                has_pause = True
        if has_punct or has_pause or is_last:
            s_text = " ".join(w["word"] for w in curr_words)
            s_start = curr_words[0]["start"]
            s_end = curr_words[-1]["end"]
            sentences.append({
                "text": s_text,
                "start": s_start,
                "end": s_end,
                "duration": round(max(0.8, s_end - s_start), 3)
            })
            curr_words = []
    return sentences


class VoiceSynthesizer:
    def __init__(self, voice_key: str = None, language: str = "en", rate: str = "+2%"):
        self.language = language.lower()
        if not voice_key or voice_key == "default":
            if self.language in ["ta", "tamil"]:
                self.voice = "ta-IN-PallaviNeural"
            else:
                self.voice = "en-US-AriaNeural"
        else:
            self.voice = VOICE_MAP.get(voice_key.lower(), voice_key)
            
        self.rate = rate

    def get_duration(self, audio_file: Path) -> float:
        if not audio_file.exists() or audio_file.stat().st_size == 0:
            return 3.0
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_file)
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return max(0.5, float(res.stdout.strip()))
        except Exception:
            return 3.0

    async def _generate_single(self, scene: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
        sid = scene["id"]
        out_mp3 = output_dir / f"{sid}.mp3"
        word_timings = []
        audio_bytes = bytearray()

        active_voice = self.voice
        if scene.get("voice"):
            active_voice = VOICE_MAP.get(str(scene["voice"]).lower().strip(), scene["voice"])

        try:
            communicate = edge_tts.Communicate(
                scene["narration"],
                active_voice,
                rate=self.rate,
                boundary="WordBoundary"
            )
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_bytes.extend(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    offset_sec = chunk["offset"] / 10_000_000.0
                    dur_sec = chunk["duration"] / 10_000_000.0
                    word_timings.append({
                        "word": chunk["text"],
                        "start": round(offset_sec, 3),
                        "end": round(offset_sec + dur_sec, 3),
                        "duration": round(dur_sec, 3)
                    })
            if audio_bytes:
                out_mp3.write_bytes(audio_bytes)
        except Exception as e:
            print(f"[Notice] edge-tts stream error for scene '{sid}': {e}")

        # CLI fallback if streaming yielded no bytes
        if not out_mp3.exists() or out_mp3.stat().st_size == 0:
            cmd = [
                "edge-tts",
                "--voice", active_voice,
                f"--rate={self.rate}",
                "--text", scene["narration"],
                "--write-media", str(out_mp3)
            ]
            try:
                proc = await asyncio.create_subprocess_exec(*cmd)
                await proc.wait()
            except Exception as e:
                print(f"[Notice] edge-tts fallback error for scene '{sid}': {e}")

        # Silent audio fallback if completely offline
        if not out_mp3.exists() or out_mp3.stat().st_size == 0:
            fallback_cmd = [
                "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                "-t", "3.0", "-q:a", "9", str(out_mp3)
            ]
            try:
                proc = await asyncio.create_subprocess_exec(
                    *fallback_cmd,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await proc.wait()
            except Exception as e:
                print(f"[Notice] Silent audio fallback error for scene '{sid}': {e}")

        dur = self.get_duration(out_mp3)
        scene["audio_file"] = str(out_mp3.resolve())
        scene["duration"] = dur
        scene["word_timings"] = word_timings
        scene["sentence_timings"] = extract_sentence_boundaries_from_words(word_timings, scene["narration"])
        return scene

    async def generate_all(self, scenes: List[Dict[str, Any]], output_dir: Path) -> List[Dict[str, Any]]:
        output_dir.mkdir(parents=True, exist_ok=True)
        sem = asyncio.Semaphore(4)

        async def _bounded_single(s):
            async with sem:
                return await self._generate_single(s, output_dir)

        tasks = [_bounded_single(s) for s in scenes]
        return await asyncio.gather(*tasks)

    def synthesize(self, scenes: List[Dict[str, Any]], output_dir: Path) -> List[Dict[str, Any]]:
        return asyncio.run(self.generate_all(scenes, output_dir))

    def synthesize_line(self, text: str, output_file: Path) -> float:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            communicate = edge_tts.Communicate(text, self.voice, rate=self.rate)
            communicate.save_sync(str(output_file))
        except Exception:
            cmd = [
                "edge-tts",
                "--voice", self.voice,
                f"--rate={self.rate}",
                "--text", text,
                "--write-media", str(output_file)
            ]
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                fallback_cmd = [
                    "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                    "-t", "3.0", "-q:a", "9", str(output_file)
                ]
                subprocess.run(fallback_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return self.get_duration(output_file)
