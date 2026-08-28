#!/usr/bin/env python3
"""Create a timestamped offline backup of demo artifacts."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKUPS_DIR = REPO_ROOT / "backups"
IST = timezone(timedelta(hours=5, minutes=30))

INCLUDE_PATHS = [
    "out",
    "frontend/public/data",
    "config",
    "docs/demo_script.md",
    "docs/REHEARSAL_CHECKLIST.md",
    "docs/FEATURE_FREEZE.md",
    "README.md",
]


def _add_tree(zf: ZipFile, root: Path, arc_prefix: str) -> int:
    count = 0
    if not root.exists():
        return 0
    if root.is_file():
        zf.write(root, arcname=arc_prefix.replace("\\", "/"))
        return 1
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(REPO_ROOT)
            zf.write(path, arcname=str(rel).replace("\\", "/"))
            count += 1
    return count


def main() -> int:
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(IST).strftime("%Y%m%d_%H%M%S")
    archive = BACKUPS_DIR / f"redzone_demo_backup_{stamp}.zip"
    manifest = {
        "created_at": datetime.now(IST).isoformat(),
        "archive": archive.name,
        "paths": INCLUDE_PATHS,
        "file_count": 0,
    }

    print(f"Creating backup: {archive}")
    with ZipFile(archive, "w", compression=ZIP_DEFLATED) as zf:
        total = 0
        for rel in INCLUDE_PATHS:
            path = REPO_ROOT / rel
            added = _add_tree(zf, path, rel)
            total += added
            print(f"  + {rel} ({added} files)")
        manifest["file_count"] = total

    manifest_path = BACKUPS_DIR / f"redzone_demo_backup_{stamp}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    size_mb = archive.stat().st_size / (1024 * 1024)
    print(f"Backup complete: {archive} ({size_mb:.2f} MB)")
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
