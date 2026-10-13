"""
Managed State Machine Asset Builder for IRAM Video.
Provides per-clip retry resilience, exponential backoff, persistent checkpointing,
and multi-tier graceful provider fallback (Primary AI -> Stock Media -> Procedural Canvas).
"""

import os
import json
import time
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger("iram_video.state_machine")


class AssetRenderState(str, Enum):
    PENDING = "PENDING"
    RENDERING = "RENDERING"
    RETRYING = "RETRYING"
    FALLING_BACK = "FALLING_BACK"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class StateMachineAssetBuilder:
    """
    Manages clip rendering with a formal state machine:
    - Retries transient GPU / API failures up to max_retries with backoff.
    - Gracefully cascades through failover tiers when a provider fails.
    - Stores persistent checkpoints on disk to allow resumes without restarting from scratch.
    """

    def __init__(
        self,
        checkpoint_dir: Path,
        max_retries: int = 3,
        initial_backoff: float = 0.5,
        resume: bool = True
    ):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_file = self.checkpoint_dir / "render_checkpoint.json"
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.resume = resume
        self.state_registry: Dict[str, Dict[str, Any]] = self._load_checkpoints()

    def _load_checkpoints(self) -> Dict[str, Dict[str, Any]]:
        if self.resume and self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data)} completed clip checkpoints from {self.checkpoint_file.name}")
                    return data
            except Exception as e:
                logger.warning(f"Could not read checkpoint file: {e}")
        return {}

    def _save_checkpoints(self):
        try:
            tmp = self.checkpoint_file.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.state_registry, f, indent=2)
            tmp.replace(self.checkpoint_file)
        except Exception as e:
            logger.warning(f"Failed to persist checkpoint: {e}")

    def render_asset_with_resilience(
        self,
        asset_id: str,
        output_path: Path,
        tier1_fn: Callable[[], Path],
        tier2_fn: Optional[Callable[[], Path]] = None,
        tier3_fn: Optional[Callable[[], Path]] = None,
        state_callback: Optional[Callable[[str, AssetRenderState, Dict[str, Any]], None]] = None
    ) -> Path:
        """
        Executes rendering for a specific asset with retry loop and graceful tier failovers.
        """
        output_path = Path(output_path)

        # 1. Check existing valid checkpoint & output file
        if self.resume and asset_id in self.state_registry:
            entry = self.state_registry[asset_id]
            if entry.get("state") == AssetRenderState.COMPLETED and output_path.exists() and output_path.stat().st_size > 10:
                logger.info(f"⚡ [RESUME] Skipping already-rendered asset {asset_id} ({output_path.name})")
                if state_callback:
                    state_callback(asset_id, AssetRenderState.COMPLETED, {"resumed": True, "path": str(output_path)})
                return output_path

        # Initialize State
        self.state_registry[asset_id] = {
            "state": AssetRenderState.PENDING,
            "attempts": 0,
            "tier": 1,
            "error": None,
            "output_path": str(output_path)
        }
        self._save_checkpoints()

        # Tier Execution Loop
        tiers = [
            (1, "Primary Generative AI", tier1_fn),
            (2, "Curated Stock Media Backup", tier2_fn),
            (3, "Programmatic Motion Canvas", tier3_fn)
        ]

        last_error = None
        for tier_num, tier_label, tier_fn in tiers:
            if not tier_fn:
                continue

            self.state_registry[asset_id]["tier"] = tier_num
            backoff = self.initial_backoff

            for attempt in range(1, self.max_retries + 1):
                self.state_registry[asset_id]["attempts"] += 1
                curr_state = AssetRenderState.RENDERING if attempt == 1 else AssetRenderState.RETRYING
                self.state_registry[asset_id]["state"] = curr_state
                self._save_checkpoints()

                if state_callback:
                    state_callback(asset_id, curr_state, {
                        "tier": tier_num,
                        "tier_label": tier_label,
                        "attempt": attempt,
                        "max_retries": self.max_retries
                    })

                try:
                    logger.info(f"▶ [{asset_id}] Executing Tier {tier_num} ({tier_label}) - Attempt {attempt}/{self.max_retries}")
                    res_path = tier_fn()
                    if res_path and Path(res_path).exists() and Path(res_path).stat().st_size > 10:
                        self.state_registry[asset_id]["state"] = AssetRenderState.COMPLETED
                        self.state_registry[asset_id]["error"] = None
                        self._save_checkpoints()

                        if state_callback:
                            state_callback(asset_id, AssetRenderState.COMPLETED, {
                                "tier": tier_num,
                                "path": str(res_path)
                            })
                        return Path(res_path)
                    else:
                        raise ValueError(f"Output file missing or empty from Tier {tier_num}")

                except Exception as exc:
                    last_error = exc
                    self.state_registry[asset_id]["error"] = str(exc)
                    self._save_checkpoints()
                    logger.warning(f"⚠️ [{asset_id}] Tier {tier_num} attempt {attempt} failed: {exc}")

                    if attempt < self.max_retries:
                        time.sleep(backoff)
                        backoff *= 2.0

            # If all retries in this tier failed, signal fallback to next tier
            logger.warning(f"🔄 [{asset_id}] Tier {tier_num} exhausted ({self.max_retries} retries). Falling back...")
            self.state_registry[asset_id]["state"] = AssetRenderState.FALLING_BACK
            self._save_checkpoints()
            if state_callback:
                state_callback(asset_id, AssetRenderState.FALLING_BACK, {
                    "failed_tier": tier_num,
                    "error": str(last_error)
                })

        # All tiers exhausted
        self.state_registry[asset_id]["state"] = AssetRenderState.FAILED
        self._save_checkpoints()
        if state_callback:
            state_callback(asset_id, AssetRenderState.FAILED, {"error": str(last_error)})
        raise RuntimeError(f"All {len(tiers)} failover tiers failed for asset {asset_id}. Last error: {last_error}")
