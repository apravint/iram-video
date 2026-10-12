"""
Short Drama & Character Consistency Engine for IRAM Video.
Inspired by Toonflow-app, dramaclaw, and ViMax.
Manages multi-scene character identity consistency, dramatic tension curves,
and agentic storyboarding across episodic drama and animated narratives.
"""

from typing import Dict, Any, List, Optional

class CharacterAnchorRegistry:
    """Maintains strict visual consistency anchors for characters across all scenes."""

    def __init__(self):
        self._characters: Dict[str, Dict[str, str]] = {}

    def register_character(
        self,
        name: str,
        role: str,
        appearance: str,
        wardrobe: str,
        voice_id: str = "default",
        traits: Optional[List[str]] = None
    ) -> Dict[str, str]:
        key = name.lower().strip()
        anchor = {
            "name": name,
            "role": role,
            "appearance": appearance,
            "wardrobe": wardrobe,
            "voice_id": voice_id,
            "traits": ", ".join(traits or []),
            "prompt_token": f"{appearance}, wearing {wardrobe}"
        }
        self._characters[key] = anchor
        return anchor

    def get_prompt_anchor(self, character_name: str) -> str:
        key = character_name.lower().strip()
        if key in self._characters:
            return self._characters[key]["prompt_token"]
        return character_name

    def list_characters(self) -> List[Dict[str, str]]:
        return list(self._characters.values())

class DramaTensionCurve:
    """Evaluates and balances the emotional pacing and dramatic tension of a screenplay."""

    @staticmethod
    def calculate_tension_curve(scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Assigns standard Hollywood dramatic tension scores (0-100) across scenes:
        - Hook / Cold Open: 75%
        - Inciting Incident: 40%
        - Escalation & Friction: 65%
        - Turning Point / Crisis: 85%
        - Climax & Catharsis: 95%
        - Resolution / Final Hook: 50%
        """
        n = len(scenes)
        if n == 0:
            return []

        annotated = []
        for i, sc in enumerate(scenes):
            progress = i / max(1, n - 1)
            # Tension bell curve peaking at 80% through the story
            if progress < 0.2:
                tension = 70 + int(progress * 25)
                beat_type = "Inciting Hook"
            elif progress < 0.6:
                tension = 50 + int((progress - 0.2) * 60)
                beat_type = "Escalation"
            elif progress < 0.85:
                tension = 80 + int((progress - 0.6) * 60)
                beat_type = "Climactic Confrontation"
            else:
                tension = 55
                beat_type = "Resolution & Cliffhanger"

            item = dict(sc)
            item["tension_score"] = min(100, max(10, tension))
            item["dramatic_beat"] = beat_type
            annotated.append(item)

        return annotated
