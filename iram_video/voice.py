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
