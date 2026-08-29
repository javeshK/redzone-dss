#!/usr/bin/env python3
"""Phase 3 scaffold — hybrid ML susceptibility training (disabled by default).

Requires labelled events in data/rudraprayag/events/ before enabling.
Do NOT set ml_enabled: true in weights.yaml without passing backtest gates.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EVENTS_DIR = REPO_ROOT / "data" / "rudraprayag" / "events"
OUT_METRICS = REPO_ROOT / "out" / "ml_metrics.json"
IST = timezone(timedelta(hours=5, minutes=30))


def main() -> int:
    print("RedZone DSS — ML Susceptibility Training (scaffold)")
    print("=" * 50)
    events_csv = EVENTS_DIR / "labelled_events.csv"
    if not events_csv.exists():
        print(f"  [info] No events dataset at {events_csv}")
        print("  Curate labelled landslide/cloudburst events before training.")
        metrics = {
            "status": "not_ready",
            "generated_at": datetime.now(IST).isoformat(),
            "ml_enabled": False,
            "note": "Awaiting labelled_events.csv in data/rudraprayag/events/",
            "minimum_precision": 0.6,
            "minimum_recall": 0.5,
            "metrics": None,
        }
        OUT_METRICS.parent.mkdir(parents=True, exist_ok=True)
        OUT_METRICS.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        print(f"  Wrote placeholder metrics to {OUT_METRICS}")
        return 0

    print("  [info] Events file found — training stub not yet implemented.")
    print("  Implement sklearn/XGBoost training when event inventory is validated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
