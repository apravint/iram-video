"""
Video Template & Genre Architecture for IRAM Video.
Provides structured directorial blueprints, pacing curves, layout sequences,
and visual formatting rules for 7 universal video genres:
- explainer: Standard deep-dive documentary (Vox, Kurzgesagt, Veritasium)
- tutorial: Step-by-step educational guide with practical milestones
- listicle: High-retention countdown (#5 through #1) with rank badges
- comparison: Head-to-head matchup (Product A vs B) with verdict
- news: Breaking broadcast bulletin with lower-third chyrons and ticker
- promo: High-energy marketing showcase with problem, solution, and CTA
- podcast: Audiogram soundbite card with waveform and speaker attribution
"""

from typing import Dict, Any, List, Optional

VIDEO_TEMPLATES = {
    "explainer": {
        "name": "Deep-Dive Explainer",
        "description": "Insightful documentary deep-dive explaining complex mechanisms with clarity and authority.",
        "default_scenes": 4,
        "default_music": "documentary",
        "default_grade": "clean",
        "structure": [
            {"role": "The Hook & Paradox", "layout": "hero_metric", "motion": "steady_push_in"},
            {"role": "The Core Architecture", "layout": "pillars", "motion": "macro_orbit"},
            {"role": "Deep Technical Breakdown", "layout": "code_or_terminal", "motion": "steady"},
            {"role": "Future Implications & Synthesis", "layout": "stack_list", "motion": "zoom_out"}
        ],
        "director_directive": (
            "TEMPLATE: EXPLAINER DOCUMENTARY.\n"
            "- Act I: Hook with an intriguing paradox or real-world friction.\n"
            "- Act II: Deconstruct the fundamental principles with clear visual anchors.\n"
            "- Act III: Walk through concrete implementation or case study.\n"
            "- Act IV: Synthesize the broader implications and future outlook.\n"
            "- Tone: Authoritative, conversational, intellectual, like Vox or Veritasium."
        )
    },
    "tutorial": {
        "name": "Step-by-Step Tutorial & How-To",
        "description": "Structured instructional walkthrough guiding the viewer from prerequisites to completed implementation.",
        "default_scenes": 5,
        "default_music": "lofi",
        "default_grade": "clean",
        "structure": [
            {"role": "Objective & Prerequisites", "layout": "hero_metric", "badge": "SETUP"},
            {"role": "Step 1: Foundation & Installation", "layout": "code_or_terminal", "badge": "STEP 1"},
            {"role": "Step 2: Core Configuration", "layout": "code_or_terminal", "badge": "STEP 2"},
            {"role": "Step 3: Verification & Execution", "layout": "code_or_terminal", "badge": "STEP 3"},
            {"role": "Summary & Pro Tips", "layout": "stack_list", "badge": "PRO TIPS"}
        ],
        "director_directive": (
            "TEMPLATE: STEP-BY-STEP TUTORIAL.\n"
            "- Scene 1: Objective — What we are building and what prerequisites are needed.\n"
            "- Scene 2: Step 1 — Initial setup, installation, or foundation.\n"
            "- Scene 3: Step 2 — Core implementation logic and configuration.\n"
            "- Scene 4: Step 3 — Testing, deployment, or verification of results.\n"
            "- Scene 5: Common pitfalls, optimization pro tips, and conclusion.\n"
            "- Include exact code snippets, terminal commands, or step numbers for each scene.\n"
            "- Tone: Encouraging, precise, pedagogical, clear."
        )
    },
    "listicle": {
        "name": "Top-N Countdown / Listicle",
        "description": "High-retention ranked countdown highlighting standout entries with rank shields and key metrics.",
        "default_scenes": 5,
        "default_music": "energetic",
        "default_grade": "vibrant",
        "structure": [
            {"role": "Viral Hook & Why It Matters", "layout": "hero_metric", "badge": "COUNTDOWN"},
            {"role": "Rank #4", "layout": "pillars", "badge": "#4"},
            {"role": "Rank #3", "layout": "pillars", "badge": "#3"},
            {"role": "Rank #2", "layout": "pillars", "badge": "#2"},
            {"role": "Rank #1 Winner & Final Takeaway", "layout": "hero_metric", "badge": "#1 WINNER"}
        ],
        "director_directive": (
            "TEMPLATE: TOP-N COUNTDOWN LISTICLE.\n"
            "- Scene 1: High-energy opening hook establishing why this ranking matters.\n"
            "- Subsequent scenes: Ranked countdown from lowest to highest (#4 -> #3 -> #2 -> #1 WINNER).\n"
            "- Each ranked scene MUST feature the entry's name, key metrics, and standout advantage.\n"
            "- Final scene: Unveil the #1 Winner with emphatic praise and summary verdict.\n"
            "- Tone: Fast-paced, punchy, engaging, high retention."
        )
    },
    "comparison": {
        "name": "Head-to-Head Comparison",
        "description": "Objective side-by-side analysis contrasting two contenders across features, performance, and trade-offs.",
        "default_scenes": 4,
        "default_music": "tech",
        "default_grade": "clean",
        "structure": [
            {"role": "The Matchup & Contenders", "layout": "comparison", "badge": "VS"},
            {"role": "Core Performance & Architecture", "layout": "comparison", "badge": "BENCHMARK"},
            {"role": "Developer Experience & Trade-offs", "layout": "comparison", "badge": "TRADEOFFS"},
            {"role": "Final Verdict & Recommendation", "layout": "hero_metric", "badge": "VERDICT"}
        ],
        "director_directive": (
            "TEMPLATE: HEAD-TO-HEAD COMPARISON.\n"
            "- Scene 1: Introduce the two contenders, their philosophies, and why the choice matters.\n"
            "- Scene 2: Direct performance/speed/cost benchmark comparison.\n"
            "- Scene 3: Ecosystem, ergonomics, and real-world trade-offs.\n"
            "- Scene 4: Clear verdict on who should pick Contender A vs Contender B.\n"
            "- Ensure cards use layout_type 'comparison' with symmetric pros/cons.\n"
            "- Tone: Objective, nuanced, data-driven, practical."
        )
    },
    "news": {
        "name": "Breaking News & Editorial Bulletin",
        "description": "Urgent broadcast news format with headline tickers, chyrons, facts, and expert analysis.",
        "default_scenes": 4,
        "default_music": "trailer",
        "default_grade": "editorial",
        "structure": [
            {"role": "Breaking Bulletin & Primary Headline", "layout": "hero_metric", "badge": "BREAKING"},
            {"role": "Verified Facts & Timeline", "layout": "stack_list", "badge": "DEVELOPING"},
            {"role": "Industry Reaction & Quotes", "layout": "pillars", "badge": "ANALYSIS"},
            {"role": "Key Takeaways & What Follows", "layout": "hero_metric", "badge": "OUTLOOK"}
        ],
        "director_directive": (
            "TEMPLATE: BREAKING NEWS & EDITORIAL BULLETIN.\n"
            "- Scene 1: Immediate breaking alert with headline, timestamp, and core event.\n"
            "- Scene 2: Timeline of verified facts and chronological developments.\n"
            "- Scene 3: Industry reaction, expert statements, or official responses.\n"
            "- Scene 4: Strategic impact, market consequences, and next milestones.\n"
            "- Include lower-third metadata and punchy journalistic headlines.\n"
            "- Tone: Urgent, authoritative, journalistic, credible."
        )
    },
    "promo": {
        "name": "Product Launch & SaaS Promo",
        "description": "High-conversion marketing showcase moving from customer pain to breakthrough product demo and CTA.",
        "default_scenes": 4,
        "default_music": "energetic",
        "default_grade": "vibrant",
        "structure": [
            {"role": "The Friction & Broken Way", "layout": "hero_metric", "badge": "THE PROBLEM"},
            {"role": "Introducing the Breakthrough", "layout": "pillars", "badge": "THE SOLUTION"},
            {"role": "Feature Superpowers & Proof", "layout": "stack_list", "badge": "FEATURES"},
            {"role": "Call-to-Action & Launch Offer", "layout": "hero_metric", "badge": "GET STARTED"}
        ],
        "director_directive": (
            "TEMPLATE: PRODUCT LAUNCH & PROMO.\n"
            "- Scene 1: Highlight the painful problem and current inefficient status quo.\n"
            "- Scene 2: Reveal the product/solution as the modern, effortless alternative.\n"
            "- Scene 3: Showcase 3 killer features with clear tangible benefits.\n"
            "- Scene 4: Irresistible Call-to-Action (CTA) urging viewers to start, star, or visit.\n"
            "- Tone: Inspiring, high energy, crisp, persuasive."
        )
    },
    "podcast": {
        "name": "Podcast Audiogram & Soundbite",
        "description": "Conversational audio showcase featuring quotes, speaker badges, soundbites, and insights.",
        "default_scenes": 3,
        "default_music": "lofi",
        "default_grade": "warm_editorial",
        "structure": [
            {"role": "Provocative Question or Quote", "layout": "hero_metric", "badge": "CLIP"},
            {"role": "Core Insight & Discussion", "layout": "pillars", "badge": "DEEP DIVE"},
            {"role": "Full Episode Invitation", "layout": "hero_metric", "badge": "FULL EPISODE"}
        ],
        "director_directive": (
            "TEMPLATE: PODCAST SOUNDBITE & AUDIOGRAM.\n"
            "- Scene 1: A powerful soundbite or provocative statement from the conversation.\n"
            "- Scene 2: Unpacking the underlying insight with conversational depth.\n"
            "- Scene 3: Memorable takeaway and invitation to hear the full episode.\n"
            "- Tone: Intimate, spontaneous, conversational, thought-provoking."
        )
    }
}

def get_template(template_name: Optional[str]) -> Dict[str, Any]:
    """Retrieves template configuration with fallback to explainer."""
    if not template_name:
        tmpl = VIDEO_TEMPLATES["explainer"]
    else:
        key = template_name.lower().strip().replace("-", "_").replace(" ", "_")
        tmpl = VIDEO_TEMPLATES.get(key, VIDEO_TEMPLATES["explainer"])
    res = dict(tmpl)
    res["default_color_grade"] = res.get("default_grade", "clean")
    res["directorial_hints"] = res.get("director_directive", "")
    return res

def list_templates() -> List[Dict[str, Any]]:
    """Returns catalog of all supported video templates."""
    catalog = []
    for k, v in VIDEO_TEMPLATES.items():
        catalog.append({
            "key": k,
            "name": v["name"],
            "description": v["description"],
            "default_scenes": v["default_scenes"],
            "default_music": v["default_music"],
            "default_grade": v["default_grade"]
        })
    return catalog
