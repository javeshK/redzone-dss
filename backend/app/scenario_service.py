"""Scenario rescoring service for rainfall factor API."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from _scenario import ALLOWED_FACTORS, compute_scenario_hazard  # noqa: E402


class ScenarioService:
    def __init__(self, out_dir: Path | None = None) -> None:
        self.out_dir = out_dir or REPO_ROOT / "out"
        self._cache: dict[str, Any] | None = None

    def _load_precomputed(self) -> dict[str, Any] | None:
        path = self.out_dir / "scenarios.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return None

    def get_rainfall_scenario(self, factor: float) -> dict[str, Any]:
        if factor not in ALLOWED_FACTORS:
            return {"error": f"factor must be one of {list(ALLOWED_FACTORS)}", "factor": factor}
        precomputed = self._load_precomputed()
        key = str(factor)
        if precomputed and key in precomputed:
            return precomputed[key]
        return compute_scenario_hazard(factor)


scenario_service = ScenarioService()
