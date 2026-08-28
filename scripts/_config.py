"""Shared configuration loader for GIS pipeline scripts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO_ROOT / "config"


def load_weights() -> dict[str, Any]:
    with open(CONFIG_DIR / "weights.yaml") as f:
        return yaml.safe_load(f)


def load_paths() -> dict[str, Any]:
    with open(CONFIG_DIR / "paths.yaml") as f:
        return yaml.safe_load(f)


def ensure_dirs(*paths: str | Path) -> None:
    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)
