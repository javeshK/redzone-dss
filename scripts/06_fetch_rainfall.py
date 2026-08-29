#!/usr/bin/env python3
"""06_fetch_rainfall.py — Refresh rainfall raster for district bbox."""

from __future__ import annotations

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import REPO_ROOT, load_paths
from download_data import download_rainfall

IST = timezone(timedelta(hours=5, minutes=30))


def main() -> None:
    paths = load_paths()
    print("RedZone DSS — Rainfall Fetch")
    print("=" * 35)
    print(f"Started: {datetime.now(IST).isoformat()}")
    entry = download_rainfall(paths)
    print(f"Result: {entry.get('source')} (live={entry.get('live')})")
    print(f"Output: {entry.get('path')}")
    print("06_fetch_rainfall.py complete.")


if __name__ == "__main__":
    main()
