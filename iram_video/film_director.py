import json
import re
import time
from typing import Dict, Any, List
from google import genai
from .director import FALLBACK_MODELS

FILM_DIRECTOR_SYSTEM_PROMPT = """
You are an award-winning Hollywood Screenwriter and Animation Film Director.
Your task is to transform the user's prompt or idea into a complete, broadcast-quality ANIMATION FILM or FEATURE SHORT screenplay.

You must design a gripping cinematic narrative with a cast of 2 speaking characters (plus occasional narrator).
The screenplay structure must follow:
- ACT I: The Anomaly / Inciting Incident (World setup, mystery begins)
- ACT II: The Convergence & Crisis (Escalating stakes, conflict, philosophical revelation)
- ACT III: The Climax & Transmutation (Final decision, breakthrough, closing resonance)

For each scene:
1. "act_title": e.g. "ACT I: THE UNSEEN PROTOCOL"
2. "setting": One of ["modern_studio", "executive_boardroom", "tech_campus", "quantum_lab", "deep_space"]
3. "time_and_place": e.g. "Global Innovation Hub — 09:00 EST"
4. "action": Brief dramatic description of visual atmosphere (1-2 sentences)
5. "dialogue": An array of 2 to 4 alternating spoken lines between the characters:
   [
     {"speaker": "CharacterName", "line": "The exact spoken sentence (concise, impactful, 12-22 words).", "emotion": "concerned/confident/happy/serious"}
   ]
6. "music_mood": One of ["documentary", "acoustic", "tech", "ambient", "trailer"]

Also provide:
- "film_title": High-impact cinematic movie title (e.g. "THE ARCHITECT: Foundations of Future Intelligence")
- "genre": e.g. "Cinematic Narrative & Tech Documentary"
- "cast": Array of 2 characters:
  [
    {"name": "Nova", "role": "Lead Architect", "character_type": "presenter", "voice_key": "female"},
    {"name": "Unit-7", "role": "Sentient Core", "character_type": "robot", "voice_key": "male"}
  ]
- "closing_quote": A profound cinematic final line before credits.
- "credits": Array of strings for rolling end credits (e.g. ["DIRECTED BY: IRAM AI Studios", "STARRING: Nova & Unit-7", "MUSIC: Hans Zimmer Synthesizer Suite"])
- "youtube_metadata": Description and 8-12 tags.

CRITICAL: Return ONLY valid JSON with no markdown wrapping or code blocks.
"""

class FilmDirector:
    def __init__(self, api_key: str = None, model: str = None):
        self.model = model
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = genai.Client()

    def direct_film(self, prompt: str, scene_count: int = 3, language: str = "en", style_hint: str = None, cast_hint: str = None) -> Dict[str, Any]:
        user_msg = f"Film Prompt / Concept: {prompt}\nTarget Scene Count: {scene_count} acts.\n"
        if style_hint:
            user_msg += f"Stylistic Tone: {style_hint}\n"
        if cast_hint:
            user_msg += f"Cast Request: {cast_hint}\n"

        if language.lower() in ["ta", "tamil"]:
            user_msg += (
                "LANGUAGE: Write all dialogue, act titles, and closing quotes in authentic, cinematic Tamil (தமிழ்).\n"
                "Technical terms or character names may remain in English/Tamil as appropriate for a Tamil sci-fi cinema film.\n"
            )
        else:
            user_msg += "LANGUAGE: Produce screenplay in English with Hollywood cinematic dialogue.\n"

        models_to_try = [self.model] if self.model else FALLBACK_MODELS
        last_error = None

        for m in models_to_try:
            try:
                response = self.client.models.generate_content(
                    model=m,
                    contents=[FILM_DIRECTOR_SYSTEM_PROMPT + "\n\n" + user_msg]
                )
                raw = response.text.strip()
                if raw.startswith("```json"):
                    raw = raw[7:]
                elif raw.startswith("```"):
                    raw = raw[3:]
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()

                try:
                    screenplay = json.loads(raw)
                    return screenplay
                except json.JSONDecodeError as e:
                    match = re.search(r"\{.*\}", raw, re.DOTALL)
                    if match:
                        return json.loads(match.group(0))
                    raise ValueError(f"Failed to parse JSON: {e}")
            except Exception as e:
                print(f"[Notice] Film director model {m} unavailable ({e}), trying fallback...")
                last_error = e
                time.sleep(1)

        raise RuntimeError(f"All models exhausted for film director: {last_error}")
