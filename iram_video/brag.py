"""
Project-to-Video 'Brag' & Viral Remixer Engine for IRAM Video.
Inspired by latent-spaces/brag, mutonby/openshorts, and hypit-ai/hypit.
Turns any codebase, GitHub repo, or project into a high-energy launch video with
command terminal simulations, architecture badges, and A/B viral hooks.
"""

import os
import re
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

class BragHarvester:
    """Inspects a software repository and extracts high-CTR launch story metrics."""

    @staticmethod
    def inspect_repository(repo_path: Path) -> Dict[str, Any]:
        repo_path = repo_path.resolve()
        info = {
            "name": repo_path.name.replace("-", " ").title(),
            "description": "",
            "features": [],
            "tech_stack": [],
            "cli_command": repo_path.name.lower(),
            "git_stats": {}
        }

        # 1. Inspect README
        readme_candidates = list(repo_path.glob("README*"))
        if readme_candidates:
            try:
                # FIX: Isolate open stream contexts cleanly using with limits
                with open(readme_candidates[0], "r", encoding="utf-8", errors="ignore") as rf:
                    text = rf.read(64000) # Limit read depth to 64KB to dodge prompt overflow traps
                # Title
                m_title = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
                if m_title:
                    info["name"] = m_title.group(1).strip()
                # First paragraph
                paragraphs = [p.strip() for p in text.split("\n\n") if p.strip() and not p.startswith("#")]
                if paragraphs:
                    info["description"] = paragraphs[0][:200].replace("\n", " ")
                # Features bullets
                bullets = re.findall(r"^[\*\-]\s+\*\*([^\*]+)\*\*:\s*(.+)$", text, re.MULTILINE)
                if not bullets:
                    bullets = re.findall(r"^[\*\-]\s+(.+)$", text, re.MULTILINE)
                for b in bullets[:6]:
                    feat_str = f"{b[0]}: {b[1]}" if isinstance(b, tuple) else str(b)
                    info["features"].append(feat_str[:90])
            except Exception:
                pass

        # 2. Inspect Tech Stack Markers
        if (repo_path / "Cargo.toml").exists() or any(repo_path.glob("**/*.rs")):
            info["tech_stack"].append("Rust")
        if (repo_path / "go.mod").exists() or any(repo_path.glob("**/*.go")):
            info["tech_stack"].append("Go")
        if (repo_path / "package.json").exists() or any(repo_path.glob("**/*.ts")):
            info["tech_stack"].append("TypeScript / Node.js")
        if (repo_path / "pyproject.toml").exists() or (repo_path / "requirements.txt").exists() or (repo_path / "setup.py").exists() or any(repo_path.glob("**/*.py")):
            info["tech_stack"].append("Python")
        if (repo_path / "Dockerfile").exists():
            info["tech_stack"].append("Docker")

        # 3. Inspect Git Log
        try:
            commits = subprocess.check_output(
                ["git", "log", "-n", "10", "--oneline"],
                cwd=str(repo_path),
                text=True,
                stderr=subprocess.DEVNULL
            ).strip().splitlines()
            info["git_stats"]["recent_commits"] = len(commits)
            info["git_stats"]["latest_commit"] = commits[0] if commits else ""
        except Exception:
            pass

        return info

    @staticmethod
    def craft_launch_prompt(info: Dict[str, Any]) -> str:
        """Formulates an explosive high-retention launch video prompt."""
        name = info.get("name", "New Project")
        desc = info.get("description", "A cutting edge software platform.")
        stack = ", ".join(info.get("tech_stack", ["Modern Architecture"]))
        feats = " | ".join(info.get("features", [])[:4])
        cmd = info.get("cli_command", "run")

        prompt = (
            f"Developer Launch Video for {name}. {desc} "
            f"Built with {stack}. Key breakthroughs: {feats}. "
            f"Terminal command: '{cmd}'. High energy, punchy tech trailer."
        )
        return prompt

class ViralHookGenerator:
    """Generates 3 distinct viral opening hooks (A/B testing variant matrix)."""

    @staticmethod
    def generate_variants(topic: str) -> List[Dict[str, str]]:
        return [
            {
                "variant": "curiosity_gap",
                "label": "The Curiosity Gap",
                "hook": f"Almost nobody knows this, but the way we handle {topic} just changed forever.",
                "vibe": "intrigue"
            },
            {
                "variant": "shock_authority",
                "label": "Direct Confrontation",
                "hook": f"Stop doing {topic} the old way. You're wasting hours without realizing it.",
                "vibe": "urgent"
            },
            {
                "variant": "insider_secret",
                "label": "The Insider Secret",
                "hook": f"Here is the exact breakthrough behind {topic} that top engineers don't talk about.",
                "vibe": "revealing"
            }
        ]
