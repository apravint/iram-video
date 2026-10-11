import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Any

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
        cmd = [
            "edge-tts",
            "--voice", self.voice,
            f"--rate={self.rate}",
            "--text", scene["narration"],
            "--write-media", str(out_mp3)
        ]
        try:
            proc = await asyncio.create_subprocess_exec(*cmd)
            await proc.wait()
        except Exception as e:
            print(f"[Notice] edge-tts error for scene '{sid}': {e}")

        if not out_mp3.exists() or out_mp3.stat().st_size == 0:
            fallback_cmd = [
                "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                "-t", "3.0", "-q:a", "9", str(out_mp3)
            ]
            subprocess.run(fallback_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        dur = self.get_duration(out_mp3)
        scene["audio_file"] = str(out_mp3.resolve())
        scene["duration"] = dur
        return scene

    async def generate_all(self, scenes: List[Dict[str, Any]], output_dir: Path) -> List[Dict[str, Any]]:
        output_dir.mkdir(parents=True, exist_ok=True)
        tasks = [self._generate_single(s, output_dir) for s in scenes]
        return await asyncio.gather(*tasks)

    def synthesize(self, scenes: List[Dict[str, Any]], output_dir: Path) -> List[Dict[str, Any]]:
        return asyncio.run(self.generate_all(scenes, output_dir))

    def synthesize_line(self, text: str, output_file: Path) -> float:
        output_file.parent.mkdir(parents=True, exist_ok=True)
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

