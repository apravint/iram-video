"""
Shotcraft & Cinematic Recipe System for IRAM Video.
Inspired by video-shotcraft, OpenMontage, and waoowaoo Hollywood production frameworks.
Provides 12 production-ready cinematic shot recipe cards with lens physics, camera movement,
and optical grading curves.
"""

from typing import Dict, Any, Tuple, Optional

SHOT_RECIPES = {
    "hero_reveal": {
        "name": "Hero Reveal",
        "description": "Slow dramatic crane push-in rising from shadow to illuminate the central subject.",
        "lens": "50mm anamorphic",
        "lighting": "Volumetric rim light with subtle warm key",
        "camera_movement": "crane_push_in",
        "prompt_enhancer": "dramatic hero reveal shot, rising camera, epic volumetric rim lighting, 8k cinematic masterpiece, 35mm film grain, 50mm anamorphic bokeh",
        "ffmpeg_filter": "zoompan=z='min(zoom+0.0018,1.25)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)*(1.1-0.1*on/{frames})':s={w}x{h}:fps={fps},eq=contrast=1.08:brightness=-0.01:saturation=1.12"
    },
    "macro_orbit": {
        "name": "Macro Orbit",
        "description": "Ultra close-up smooth orbital sweep with shallow depth of field.",
        "lens": "100mm macro",
        "lighting": "Softbox studio rim light with specularity",
        "camera_movement": "orbital_pan",
        "prompt_enhancer": "extreme macro orbital camera sweep, 100mm macro lens, ultra shallow depth of field, micro textures, specular reflections, 8k resolution",
        "ffmpeg_filter": "zoompan=z=1.18:d={frames}:x='(iw-iw/zoom)*(0.5+0.5*sin(2*3.14159*on/{frames}))':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps},eq=contrast=1.06:saturation=1.14"
    },
    "speed_ramp": {
        "name": "Speed Ramp Drift",
        "description": "High-velocity dolly drift that snaps into crisp slow-motion focus on the climax.",
        "lens": "35mm prime",
        "lighting": "High-contrast dynamic neon and rim backlight",
        "camera_movement": "speed_ramp",
        "prompt_enhancer": "high speed ramp cinematic dolly shot, fast whip forward decelerating into slow motion, motion blur streaks, razor sharp focal point, 8k",
        "ffmpeg_filter": "zoompan=z='1.0+0.16*(3*pow(on/{frames},2)-2*pow(on/{frames},3))':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps},eq=contrast=1.10:saturation=1.08"
    },
    "isometric_exploded": {
        "name": "Isometric Exploded Architecture",
        "description": "Technical isometric perspective revealing layers, code nodes, or structural blueprints.",
        "lens": "Orthographic telephoto",
        "lighting": "Clean ambient occlusion with cyber accent illumination",
        "camera_movement": "isometric_drift",
        "prompt_enhancer": "isometric 3D technical exploded architecture view, glowing holographic layers, clean wireframes, high-tech engineering schematic, octane render 8k",
        "ffmpeg_filter": "zoompan=z=1.08:d={frames}:x='(iw-iw/zoom)*(on/{frames})':y='(ih-ih/zoom)*(1-on/{frames})':s={w}x{h}:fps={fps},eq=contrast=1.07:saturation=1.15"
    },
    "dutch_angle_tension": {
        "name": "Dutch Angle Tension",
        "description": "Tilted camera with high-contrast chiaroscuro shadows and psychological stakes.",
        "lens": "28mm wide-angle",
        "lighting": "Chiaroscuro side lighting with deep obsidian shadows",
        "camera_movement": "tilted_slow_push",
        "prompt_enhancer": "dutch angle tilted cinematic shot, tense psychological atmosphere, high contrast chiaroscuro lighting, deep shadows, 28mm wide angle, cinematic film still",
        "ffmpeg_filter": "zoompan=z='min(zoom+0.0012,1.18)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps},eq=contrast=1.14:brightness=-0.03:saturation=0.96"
    },
    "terminal_glitch_scan": {
        "name": "Terminal Cyber Scan",
        "description": "Holographic telemetry scan with glowing phosphor code and telemetry grids.",
        "lens": "Digital anamorphic",
        "lighting": "CRT phosphor glow (cyan/green/magenta)",
        "camera_movement": "horizontal_scan",
        "prompt_enhancer": "futuristic hacker terminal HUD scan, glowing phosphor typography, neon telemetry lines, digital matrix reflection, cyberpunk aesthetic 8k",
        "ffmpeg_filter": "zoompan=z=1.05:d={frames}:x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*(on/{frames})':s={w}x{h}:fps={fps},eq=contrast=1.12:saturation=1.20"
    },
    "split_comparison": {
        "name": "Split-Screen Contrast",
        "description": "Dynamic split composition contrasting traditional vs modernized execution.",
        "lens": "50mm dual",
        "lighting": "Dichroic dual color wash (orange vs teal)",
        "camera_movement": "lateral_split",
        "prompt_enhancer": "cinematic split screen comparison, side-by-side contrast, teal and orange complementary lighting, balanced dual focal points, 8k",
        "ffmpeg_filter": "zoompan=z='1.02+0.06*(on/{frames})':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps},eq=contrast=1.05:saturation=1.10"
    },
    "broll_whip_pan": {
        "name": "B-Roll Whip Pan",
        "description": "High velocity lateral whip transition seamlessly linking two geographic beats.",
        "lens": "24mm documentary",
        "lighting": "Golden hour daylight",
        "camera_movement": "whip_pan",
        "prompt_enhancer": "high energy documentary whip pan, rapid camera sweep across cityscape, natural sunlight, cinematic motion blur, authentic 4k",
        "ffmpeg_filter": "zoompan=z=1.14:d={frames}:x='(iw-iw/zoom)*(on/{frames})':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps},eq=contrast=1.06:saturation=1.10"
    }
}

def get_shot_recipe(recipe_key: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve recipe card with default fallback."""
    if not recipe_key:
        return SHOT_RECIPES["hero_reveal"]
    clean_key = recipe_key.lower().strip().replace(" ", "_").replace("-", "_")
    return SHOT_RECIPES.get(clean_key, SHOT_RECIPES["hero_reveal"])

def build_recipe_filter(recipe_key: str, frames: int, w: int, h: int, fps: int = 30) -> str:
    """Renders the exact FFmpeg video filtergraph for the selected recipe card."""
    recipe = get_shot_recipe(recipe_key)
    raw_filter = recipe.get("ffmpeg_filter", "")
    return raw_filter.format(frames=frames, w=w, h=h, fps=fps)
