import json
import os
import re
from typing import Dict, Any
from google import genai

DIRECTOR_SYSTEM_PROMPT = """
You are an expert AI Video Producer and Creative Director.
Your task is to transform any user topic, request, or brief into a structured, broadcast-quality video screenplay.

You must design a sequence of visual scenes (typically 3 to 8 scenes depending on depth) that tell a compelling story.
For each scene, you provide:
1. "id": e.g. "scene_1", "scene_2", ...
2. "heading": A punchy uppercase header (max 45 chars)
3. "subheading": A clean explanatory subtitle (max 85 chars)
4. "layout_type": One of:
   - "pillars": 2 or 3 vertical feature cards side-by-side
   - "comparison": 2 comparative cards (e.g. Traditional vs Modern, Pros vs Cons)
   - "code_or_terminal": A title card with a terminal command or code block simulation and callouts
   - "stack_list": 3 to 4 horizontal layer rows (good for architectures or steps)
   - "hero_metric": A big metric/concept callout card on one side and bullet details on the other
5. "cards": Array of 1 to 4 card objects:
   - "title": Card title (string)
   - "subtitle": Card subtitle (optional string)
   - "badge": Short badge text (optional, e.g. "Rust", "Core", "Speed")
   - "bullets": Array of bullet points (each 1-2 sentences, max 90 chars per bullet)
6. "narration": The EXACT spoken voiceover script for the narrator.
   - Natural, highly engaging, professional tone.
   - Paced around 35 to 55 words per scene (approx 15-25 seconds spoken).
   - Conversational, authoritative, no robotic fluff.

Also provide:
- "video_title": High-CTR, compelling YouTube video title (max 75 chars)
- "theme_palette": Suggested color scheme:
  - "bg": [r, g, b] (dark background, e.g. [10, 14, 24])
  - "accent": [r, g, b] (primary glow, e.g. [0, 229, 255])
  - "secondary": [r, g, b] (secondary accent, e.g. [168, 85, 247] or [0, 255, 136])
  - "card_bg": [r, g, b] (e.g. [16, 24, 42])
- "youtube_metadata":
  - "description": A complete, ready-to-paste YouTube description with chapter placeholders
  - "tags": Array of 8-15 relevant YouTube tags

CRITICAL: Return ONLY valid JSON with no markdown formatting or code blocks.
"""

class Director:
    def __init__(self, api_key: str = None, model: str = "gemini-3.8-flash"):
        self.model = model
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = genai.Client()

    def direct(self, prompt: str, scene_count: int = None, style_hint: str = None, language: str = "en") -> Dict[str, Any]:
        """Queries Google Gemini 3.8 Flash to outline and write the complete video screenplay in English or Tamil."""
        user_msg = f"User Prompt / Video Topic: {prompt}\n"
        if scene_count:
            user_msg += f"Target Scene Count: {scene_count} scenes.\n"
        if style_hint:
            user_msg += f"Style / Tone Preference: {style_hint}\n"

        if language.lower() in ["ta", "tamil"]:
            user_msg += (
                "LANGUAGE REQUIREMENT: Produce the ENTIRE screenplay in Tamil (தமிழ்).\n"
                "- Write video_title, headings, subheadings, cards titles, bullets, and narration in natural, high-quality, fluent Tamil (தமிழ்).\n"
                "- Spoken narration must be written in clear spoken/standard Tamil suitable for Tamil YouTube tech channels.\n"
                "- Keep technical terms, acronyms, or code in English/Tanglish where standard (e.g. Linux, Python, AI, API).\n"
            )
        else:
            user_msg += "LANGUAGE REQUIREMENT: Produce the screenplay in English.\n"

        response = self.client.models.generate_content(
            model=self.model,
            contents=[DIRECTOR_SYSTEM_PROMPT + "\n\n" + user_msg]
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
        except json.JSONDecodeError as e:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                screenplay = json.loads(match.group(0))
            else:
                raise ValueError(f"Failed to parse Google Gemini screenplay JSON: {e}\nRaw output: {raw[:300]}")

        return screenplay
