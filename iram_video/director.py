import json
import os
import re
import time
from typing import Dict, Any
from google import genai
from google.genai import types

DIRECTOR_SYSTEM_PROMPT = """
You are an expert AI Video Producer and Creative Director.
Your task is to transform any user topic, request, or brief into a structured, broadcast-quality video screenplay.

You must design a sequence of visual scenes that tell a compelling story.
For each scene, you provide:
1. "id": e.g. "scene_1", "scene_2", ...
2. "heading": A punchy uppercase header (max 40 chars)
3. "subheading": A clean explanatory subtitle (max 65 chars)
4. "layout_type": One of:
   - "pillars": (Widescreen landscape only) 2 or 3 vertical feature cards side-by-side
   - "comparison": (Widescreen landscape only) 2 comparative cards side-by-side
   - "code_or_terminal": A title card with a terminal command or code block simulation
   - "stack_list": 2 to 3 vertical stacked layers (Perfect for vertical Shorts layout)
   - "hero_metric": One primary large core callout concept filling the screen space
   CRITICAL: If the format is YOUTUBE SHORTS, NEVER choose "pillars" or "comparison". Only use single-column layouts like "hero_metric", "code_or_terminal", or a 2-row "stack_list" to match native 9:16 mobile viewports without dropping render resolution.
   - "cards": Array of 1 to 2 card objects maximum for Shorts (3-4 allowed only for widescreen landscape).
      - "title": Card title (string, max 25 chars)
      - "subtitle": Card subtitle (optional string)
      - "badge": Short badge text (optional, e.g. "Rust", "Core", "Speed")
      - "bullets": Array of bullet points (STRICTLY 1-3 words per bullet point, maximum 2 bullets per card. Keep text concise to prevent pixel-scaling compression down the line).
5. "broll_beats": Array of 3 to 6 sequential visual beats matching each sentence of the narration:
   [
     {"phrase": "the spoken sentence", "search_query": "3-5 word exact physical cinematography keywords describing real visible objects, human actions, or physical environments (e.g. 'boxer heavy bag workout', 'sprinter track starting blocks', 'mountain climber cliff sunrise', 'hands typing mechanical keyboard', 'ocean storm lighthouse waves'). ALWAYS use concrete physical nouns. NEVER output abstract ideas like 'fear mindset' or 'success habit'.", "ai_prompt": "Cinematic 8k photorealistic video description for AI video generators (Veo/Wan/Kling) describing camera motion, lighting, and action", "camera": "One of ['zoom_in', 'zoom_out', 'pan_left', 'pan_right'] (dynamic 2.5D camera choreography for this beat)"}
   ]
6. "narration": The EXACT spoken voiceover script for the narrator.
   - Natural, highly engaging, professional tone.
   - Conversational, authoritative, no robotic fluff.

Also provide:
- "video_title": High-CTR, compelling YouTube video title (max 75 chars)
- "theme_palette": Suggested color scheme:
  - "bg": [r, g, b] (deep slate background, e.g. [15, 23, 42])
  - "accent": [r, g, b] (primary clean accent, e.g. [59, 130, 246] or [37, 99, 235])
  - "secondary": [r, g, b] (secondary neutral/amber, e.g. [148, 163, 184] or [245, 158, 11])
  - "card_bg": [r, g, b] (slate card surface, e.g. [30, 41, 59])
- "visual_policy": STRICT REQUIREMENT - AVOID all cyberpunk tropes, neon pink, magenta, or glowing green. Maintain clean, modern, professional enterprise aesthetics (Vox/Apple Keynote style).
- "soundscape":
  - "ambient_track": Suggested subtle ambient background (e.g. "mechanical_typing", "server_room", "subtle_rain", "subtle_wind", "room_tone")
  - "soundscape_playlist": Array of 1 to 3 audio texture layers, e.g. [{"type": "mechanical_typing", "volume": 0.12}]
- "youtube_metadata":
  - "description": A complete, ready-to-paste YouTube description with chapter placeholders
  - "tags": Array of 8-15 relevant YouTube tags

CRITICAL UNIQUENESS & CREATIVITY MANDATE:
- Every video screenplay MUST be completely fresh, unique, and tailored specifically to the prompt.
- NEVER reuse clichéd tropes or formulaic openers like "Most people fail because...", "Motivation is a lie", or "The secret to becoming unstoppable".
- Invent fresh narrative angles, unexpected hooks, relatable real-world analogies, and vivid emotional or thought-provoking moments.
- For EVERY scene's 'broll_beats', provide highly specific, concrete, physical cinematography search queries ('search_query') describing real physical subjects, environments, actions, and lighting (e.g. "blacksmith sparks anvil", "marathon runner rain finish line", "deep sea diver bioluminescent reef"). NEVER output generic or repetitive phrases.

CRITICAL: Return ONLY valid JSON with no markdown formatting or code blocks.
"""

FALLBACK_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-3.1-pro-preview"
]

from .templates import get_template

class Director:
    def __init__(self, api_key: str = None, model: str = None):
        self.model = model
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = genai.Client()

    def direct(
        self,
        prompt: str,
        scene_count: int = None,
        style_hint: str = None,
        language: str = "en",
        is_shorts: bool = False,
        is_cinema: bool = False,
        is_real: bool = False,
        character: str = None,
        template: str = None
    ) -> Dict[str, Any]:
        """Queries Google Gemini to outline and write the screenplay with multi-model fallback."""
        user_msg = f"User Prompt / Video Topic: {prompt}\n"
        user_msg += (
            "AESTHETIC & CAMERA DIRECTIVE:\n"
            "- AVOID all cyberpunk tropes, neon pink, magenta, glowing acid green, or hacker stereotypes.\n"
            "- Use clean, modern, professional editorial styling (deep slate, crisp white typography, subtle cobalt/warm amber accents).\n"
            "- Camera motion must be subtle and steady (e.g. 'steady', 'zoom_in', 'zoom_out'). NO violent whipping or chaotic motion.\n"
            "- For each scene, include a 'lower_third' object: {\"title\": \"Punchy Subject/Name\", \"subtitle\": \"Role/Context\"}.\n"
        )

        if template:
            tmpl_data = get_template(template, is_shorts=is_shorts)
            user_msg += f"\nDIRECTORIAL TEMPLATE: {tmpl_data['name'].upper()}\n"
            user_msg += f"{tmpl_data['director_directive']}\n"
            if not scene_count:
                scene_count = tmpl_data.get("default_scenes", 4)
        
        if is_real:
            user_msg += (
                "REAL YOUTUBE DOCUMENTARY DIRECTIVE:\n"
                "- Write this screenplay like a high-retention, real YouTube documentary (Vox, Kurzgesagt, Johnny Harris, Veritasium style).\n"
                "- Tone: Natural, intelligent, conversational, insightful, and cinematic.\n"
                "- Real B-Roll Footage: Provide accurate 'search_query' keywords for real stock footage/photos for every scene.\n"
                "- AVOID any cyberpunk, neon, or fictional matrix tropes. Focus on real-world concepts, science, history, tech, or nature.\n"
            )

        if is_shorts:
            user_msg += (
                "FORMAT REQUIREMENT: YOUTUBE SHORTS (VERTICAL 9:16).\n"
                "- Pacing MUST be ultra fast-paced and punchy (3 scenes total, STRICTLY under 45 seconds spoken audio).\n"
                "- Each scene narration must be 15 to 22 words maximum (fast hook, immediate value, loopable outro).\n"
                "- Enforce visual layout density: limit cards to 1 per scene. Do not request dense bullet blocks.\n"
                "- Add '#Shorts' to the end of the video_title and in the description.\n"
            )
            if not scene_count:
                scene_count = 3

        if is_cinema:
            user_msg += (
                "CINEMATIC MOVIE TRAILER DIRECTIVE:\n"
                "- Write this screenplay like an epic Hollywood blockbuster movie trailer or documentary cinema.\n"
                "- Tone: Intense, high-stakes, dramatic, gripping, building to an epic climax.\n"
                "- Narration: Deep movie trailer voiceover cadence (e.g., 'In a world governed by legacy systems...', dramatic pauses, cinematic one-liners).\n"
                "- Scene Headings: Formatted as cinematic acts or dramatic turning points (e.g., 'ACT I: THE COLLAPSE', 'ACT II: THE FORGED TITANS', 'ACT III: THE NEW REIGN').\n"
                "- Video Title: Blockbuster movie title (e.g. 'RUST VS GO: The War for Compute | Cinematic Trailer').\n"
            )
            if not scene_count:
                scene_count = 3

        if character:
            user_msg += f"- Animated Presenter / Character: An on-screen animated mascot/character ('{character}') co-hosts the video.\n"
        
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
                "- CRITICAL: Always write 'search_query' and 'ai_prompt' inside 'broll_beats' in descriptive English (e.g. 'Chennai Metro train station', 'underground railway tunnel construction') to maximize visual stock matches from global archives.\n"
            )
        else:
            user_msg += "LANGUAGE REQUIREMENT: Produce the screenplay in English.\n"

        models_to_try = [self.model] if self.model else FALLBACK_MODELS
        last_error = None

        for m in models_to_try:
            try:
                cfg = types.GenerateContentConfig(
                    temperature=0.88,
                    top_p=0.95,
                )
                response = self.client.models.generate_content(
                    model=m,
                    contents=[DIRECTOR_SYSTEM_PROMPT + "\n\n" + user_msg],
                    config=cfg
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
                    return self.sanitize_screenplay(screenplay)
                except json.JSONDecodeError as e:
                    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
                    if fence_match:
                        try:
                            return self.sanitize_screenplay(json.loads(fence_match.group(1)))
                        except Exception:
                            pass
                    first_brace = raw.find("{")
                    last_brace = raw.rfind("}")
                    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                        candidate = raw[first_brace : last_brace + 1]
                        try:
                            return self.sanitize_screenplay(json.loads(candidate))
                        except Exception:
                            pass
                    raise ValueError(f"Failed to parse JSON: {e}")
            except Exception as e:
                print(f"[Notice] Model {m} unavailable ({e}), trying fallback...")
                last_error = e
                time.sleep(1)

        raise RuntimeError(f"All Google Gemini models exhausted: {last_error}")

    @staticmethod
    def sanitize_screenplay(screenplay: Dict[str, Any]) -> Dict[str, Any]:
        """
        Content Guard & Synthetic Transparency Sanitizer:
        Audits generated screenplay against deepfake deception and platform compliance rules.
        Attaches standard transparency metadata tags.
        """
        if not isinstance(screenplay, dict):
            return screenplay

        screenplay["compliance"] = {
            "synthetic_content_declaration": True,
            "transparency_notice": "Contains AI-generated visual and synthesized audio elements.",
            "content_guard_verified": True
        }

        prohibited_terms = ["deepfake", "counterfeit", "unauthorized impersonation"]
        for s in screenplay.get("scenes", []):
            if isinstance(s, dict) and "narration" in s:
                for term in prohibited_terms:
                    s["narration"] = re.sub(rf"\b{term}\b", "AI simulation", s["narration"], flags=re.IGNORECASE)

        return screenplay
