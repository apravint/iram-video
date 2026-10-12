"""
Soundscape Designer & Hollywood Audio Direction for IRAM Video.
Inspired by apravint/Video-Editor AI Soundscape Designer and gyoridavid/short-video-maker.
Analyzes scene action, emotional arcs, and pacing to produce bespoke acoustic/synth score design.
"""

import os
from typing import Dict, Any, Optional

try:
    from google import genai
except ImportError:
    genai = None

from .director import FALLBACK_MODELS

class SoundscapeAdvisor:
    """Designs AI audio soundscapes and musical direction for video scenes."""

    @staticmethod
    def design_soundscape(scene_prompt: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Uses Gemini Flash to analyze scene narrative and prescribe custom soundtrack & foley cues.
        """
        prompt_text = (
            f"You are a master Hollywood film composer and sound designer.\n"
            f"Given this video scene prompt: \"{scene_prompt}\"\n"
            f"Provide a concise audio direction in JSON format with:\n"
            f"- \"tempo_bpm\": integer between 60 and 130\n"
            f"- \"primary_instrument\": e.g. 'acoustic guitar', 'subtle piano', 'analog synth pad', 'orchestral strings'\n"
            f"- \"atmosphere\": e.g. 'warm, contemplative, and expansive'\n"
            f"- \"foley_cues\": array of 2-3 ambient sound effects (e.g. ['soft mechanical clicks', 'subtle room reverb'])\n"
            f"- \"recommended_mood\": one of ['documentary', 'acoustic', 'tech', 'ambient', 'lofi', 'trailer']\n"
            f"Return ONLY valid JSON with no markdown wrapping."
        )

        key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if key and genai:
            for model in FALLBACK_MODELS[:3]:
                try:
                    client = genai.Client(api_key=key)
                    resp = client.models.generate_content(model=model, contents=prompt_text)
                    txt = resp.text.strip()
                    if txt.startswith("```"):
                        txt = txt.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                    import json
                    data = json.loads(txt)
                    return data
                except Exception:
                    continue

        # Procedural fallback based on keyword analysis
        p_low = scene_prompt.lower()
        if any(k in p_low for k in ["code", "software", "ai", "digital", "system", "tech"]):
            return {
                "tempo_bpm": 84,
                "primary_instrument": "minimalist marimba & subtle analog sub-bass",
                "atmosphere": "intelligent, forward-looking, and focused",
                "foley_cues": ["subtle keyboard keystrokes", "soft ambient data hum"],
                "recommended_mood": "tech"
            }
        elif any(k in p_low for k in ["epic", "trailer", "battle", "cosmos", "future", "blockbuster"]):
            return {
                "tempo_bpm": 96,
                "primary_instrument": "deep orchestral brass & rising synthesizer drone",
                "atmosphere": "cinematic grandeur with rising stakes",
                "foley_cues": ["subtle sub-bass impact", "atmospheric whoosh"],
                "recommended_mood": "trailer"
            }
        elif any(k in p_low for k in ["nature", "history", "human", "culture", "acoustic", "life"]):
            return {
                "tempo_bpm": 72,
                "primary_instrument": "warm fingerpicked acoustic guitar & gentle cello",
                "atmosphere": "warm, organic, authentic, and reflective",
                "foley_cues": ["natural room tone", "soft breeze"],
                "recommended_mood": "acoustic"
            }
        else:
            return {
                "tempo_bpm": 78,
                "primary_instrument": "clean upright piano & warm ambient pad",
                "atmosphere": "informative, elegant, and modern editorial",
                "foley_cues": ["gentle tape warmth", "clean room presence"],
                "recommended_mood": "documentary"
            }

    @classmethod
    def advise_soundscape(cls, scene_prompt: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        """Convenience method returning normalized soundscape attributes."""
        data = cls.design_soundscape(scene_prompt, api_key=api_key)
        res = dict(data)
        if "bgm_style" not in res:
            res["bgm_style"] = res.get("recommended_mood", "documentary").title()
        if "bgm_mood" not in res:
            res["bgm_mood"] = res.get("atmosphere", "Contemplative")
        if "instruments" not in res:
            res["instruments"] = [res.get("primary_instrument", "Acoustic Piano & Strings")]
        return res
