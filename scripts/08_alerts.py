#!/usr/bin/env python3
"""08_alerts.py — Rule-based explainable alerts for high-risk habitations."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import REPO_ROOT, load_paths

IST = timezone(timedelta(hours=5, minutes=30))

RAINFALL_THRESHOLD = 0.65
H_HAB_THRESHOLD = 0.70
PCT_RED_THRESHOLD = 30.0


def generate_alerts(paths: dict) -> dict:
    hab_path = REPO_ROOT / paths["out"]["habitations"]
    if not hab_path.exists():
        return {"generated_at": datetime.now(IST).isoformat(), "alerts": []}

    habs = json.loads(hab_path.read_text(encoding="utf-8"))
    alerts = []

    for feat in habs.get("features", []):
        props = feat["properties"]
        h = props.get("h", 0)
        h_ff = props.get("h_ff", 0)
        pct_red = props.get("pct_red", 0)
        priority = props.get("priority", "Monitor")
        reasons = []

        if h_ff >= RAINFALL_THRESHOLD:
            reasons.append(
                f"Flash-flood hazard H_ff={h_ff:.2f} exceeds threshold {RAINFALL_THRESHOLD} "
                "(elevated rainfall / stream proximity)"
            )
        if h >= H_HAB_THRESHOLD:
            reasons.append(
                f"Multi-hazard H={h:.2f} exceeds threshold {H_HAB_THRESHOLD}"
            )
        if pct_red >= PCT_RED_THRESHOLD:
            reasons.append(
                f"{pct_red:.0f}% of 300 m buffer in red zone (threshold {PCT_RED_THRESHOLD}%)"
            )
        if priority == "Immediate":
            reasons.append("Priority class Immediate — relocation screening recommended")

        if reasons:
            severity = "high" if priority == "Immediate" or h >= 0.80 else "medium"
            alerts.append({
                "id": f"ALERT_{props['id']}",
                "habitation_id": props["id"],
                "habitation_name": props["name"],
                "severity": severity,
                "priority": priority,
                "h": h,
                "h_ff": h_ff,
                "pct_red": pct_red,
                "reasons": reasons,
                "action": "Review relocation recommendation and monitor rainfall forecasts",
            })

    alerts.sort(key=lambda a: (-a["h"], -a["pct_red"]))
    return {
        "generated_at": datetime.now(IST).isoformat(),
        "thresholds": {
            "h_ff": RAINFALL_THRESHOLD,
            "h_hab": H_HAB_THRESHOLD,
            "pct_red": PCT_RED_THRESHOLD,
        },
        "alert_count": len(alerts),
        "alerts": alerts,
    }


def main() -> None:
    paths = load_paths()
    print("Generating rule-based alerts...")
    data = generate_alerts(paths)
    out_path = REPO_ROOT / paths["out_dir"] / "alerts.json"
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"  {data['alert_count']} alerts -> {out_path}")

    public_path = REPO_ROOT / paths["public_data_dir"] / "alerts.json"
    public_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print("08_alerts.py complete.")


if __name__ == "__main__":
    main()
