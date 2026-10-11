import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Any

VOICE_MAP = {
    "aria": "en-US-AriaNeural",            # Female: Clear, confident, positive (Default)
    "jenny": "en-US-JennyNeural",          # Female: Friendly, conversational
    "emma": "en-US-EmmaNeural",            # Female: Cheerful, clear
    "christopher": "en-US-ChristopherNeural", # Male: Authoritative, tech narrator
    "guy": "en-US-GuyNeural",              # Male: Energetic, passionate
    "brian": "en-US-BrianNeural",          # Male: Casual, approachable
    "eric": "en-US-EricNeural"             # Male: Rational, technical
}

class VoiceSynthesizer:
    def __init__(self, voice_key: str = "aria", rate: str = "+2%"):
        self.voice = VOICE_MAP.get(voice_key.lower(), voice_key)
        self.rate = rate

    def get_duration(self, audio_file: Path) -> float:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_file)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(res.stdout.strip())

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
        proc = await asyncio.create_subprocess_exec(*cmd)
        await proc.wait()
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
