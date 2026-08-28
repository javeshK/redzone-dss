#!/usr/bin/env python3
"""Run automated demo rehearsal — validate, test, build, backup."""

from __future__ import annotations

import json
import subprocess
import sys
import platform
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
IST = timezone(timedelta(hours=5, minutes=30))


def run_step(name: str, cmd: list[str] | str, cwd: Path | None = None) -> dict:
    print(f"\n--- {name} ---")
    use_shell = isinstance(cmd, str) or (platform.system() == "Windows" and cmd and cmd[0] in ("npm", "npx"))
    if use_shell and isinstance(cmd, list):
        cmd = " ".join(cmd)
    result = subprocess.run(
        cmd,
        cwd=cwd or REPO_ROOT,
        capture_output=True,
        text=True,
        shell=use_shell,
    )
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip())
    ok = result.returncode == 0
    print(f"{'PASS' if ok else 'FAIL'}: {name}")
    return {"step": name, "ok": ok, "returncode": result.returncode}


def main() -> int:
    python = sys.executable
    steps: list[dict] = []

    steps.append(run_step("Export sync", [python, str(SCRIPTS / "05_export.py")], SCRIPTS))
    steps.append(run_step("Validate demo", [python, str(SCRIPTS / "validate_demo.py")], SCRIPTS))
    steps.append(run_step("Offline static test", [python, str(SCRIPTS / "offline_demo_test.py")], SCRIPTS))
    steps.append(run_step("Backend tests", [python, "-m", "pytest", "tests/", "-q"], REPO_ROOT / "backend"))
    steps.append(run_step("Frontend build", ["npm", "run", "build"], REPO_ROOT / "frontend"))
    steps.append(run_step("Offline static test (post-build)", [python, str(SCRIPTS / "offline_demo_test.py")], SCRIPTS))
    steps.append(run_step("Capture API snapshots", [python, str(SCRIPTS / "capture_demo_snapshots.py")], SCRIPTS))
    steps.append(run_step("Create backup", [python, str(SCRIPTS / "backup_demo.py")], SCRIPTS))

    report = {
        "rehearsal_at": datetime.now(IST).isoformat(),
        "automated": True,
        "steps": steps,
        "passed": all(s["ok"] for s in steps),
    }
    report_path = REPO_ROOT / "out" / "rehearsal_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n" + "=" * 40)
    if report["passed"]:
        print("REHEARSAL AUTOMATION: PASSED")
        print()
        print("Manual steps remaining (×3 run-throughs):")
        print("  1. Follow docs/REHEARSAL_CHECKLIST.md")
        print("  2. Record screen capture for video backup")
        print("  3. Take screenshots of Overview, Map, Habitation, Planner")
        print(f"  Report: {report_path}")
        return 0

    print("REHEARSAL AUTOMATION: FAILED")
    for s in steps:
        if not s["ok"]:
            print(f"  - {s['step']}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
