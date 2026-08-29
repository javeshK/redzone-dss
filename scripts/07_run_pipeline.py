#!/usr/bin/env python3
"""07_run_pipeline.py — Orchestrate rainfall fetch + pipeline 01-05 + alerts."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import REPO_ROOT, load_paths

IST = timezone(timedelta(hours=5, minutes=30))
SCRIPTS = Path(__file__).resolve().parent


def run_script(name: str) -> dict:
    path = SCRIPTS / name
    started = datetime.now(IST)
    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    ended = datetime.now(IST)
    ok = result.returncode == 0
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip())
    status = "ok" if ok else "failed"
    print(f"  [{status.upper()}] {name}")
    return {
        "script": name,
        "ok": ok,
        "returncode": result.returncode,
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "duration_s": round((ended - started).total_seconds(), 1),
    }


def main() -> int:
    paths = load_paths()
    out_dir = REPO_ROOT / paths["out_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)

    pipeline_start = datetime.now(IST)
    print("RedZone DSS — Full Pipeline Run")
    print("=" * 40)

    steps = [
        "06_fetch_rainfall.py",
        "01_preprocess.py",
        "02_risk_engine.py",
        "03_vuln_engine.py",
        "04_relocation.py",
        "05_export.py",
        "08_alerts.py",
        "09_export_pdf.py",
    ]

    step_results = []
    all_ok = True
    for script in steps:
        print(f"\n--- {script} ---")
        step = run_script(script)
        step_results.append(step)
        if not step["ok"]:
            all_ok = False

    pipeline_end = datetime.now(IST)
    run_log = {
        "pipeline_version": "2.0.0",
        "started_at": pipeline_start.isoformat(),
        "ended_at": pipeline_end.isoformat(),
        "duration_s": round((pipeline_end - pipeline_start).total_seconds(), 1),
        "success": all_ok,
        "steps": step_results,
    }
    log_path = out_dir / "run_log.json"
    log_path.write_text(json.dumps(run_log, indent=2), encoding="utf-8")
    print(f"\nRun log: {log_path}")
    print(f"Pipeline {'PASSED' if all_ok else 'FAILED'} in {run_log['duration_s']}s")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
