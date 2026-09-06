#!/usr/bin/env python3
"""One-shot: shrink bloated map GeoJSON for fast frontend load (no full pipeline)."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import REPO_ROOT, load_paths
from _district import filter_rudraprayag

try:
    import geopandas as gpd
except ImportError:
    print("geopandas required")
    sys.exit(1)

MAX_LANDSLIDES = 500
MAX_STREAMS = 300


def thin_district(path: Path) -> int:
    gdf = gpd.read_file(path)
    before = len(gdf)
    gdf = filter_rudraprayag(gdf)
    gdf.to_file(path, driver="GeoJSON")
    return before, len(gdf)


def thin_points(path: Path, max_n: int) -> int:
    gdf = gpd.read_file(path)
    before = len(gdf)
    if before > max_n:
        gdf = gdf.sample(max_n, random_state=42)
        gdf.to_file(path, driver="GeoJSON")
    return before, len(gdf)


def main() -> int:
    paths = load_paths()
    out = REPO_ROOT / paths["out_dir"]
    public = REPO_ROOT / paths["public_data_dir"]

    district_path = out / "district.geojson"
    if district_path.exists():
        b, a = thin_district(district_path)
        print(f"district: {b} -> {a} features")

    ls_path = out / "landslides.geojson"
    if ls_path.exists():
        b, a = thin_points(ls_path, MAX_LANDSLIDES)
        print(f"landslides: {b} -> {a} features")

    st_path = out / "streams.geojson"
    if st_path.exists():
        b, a = thin_points(st_path, MAX_STREAMS)
        print(f"streams: {b} -> {a} features")

    for name in ("district.geojson", "landslides.geojson", "streams.geojson", "red_zones.geojson"):
        src = out / name
        if src.exists():
            shutil.copy2(src, public / name)
            mb = src.stat().st_size / 1024 / 1024
            print(f"  synced {name} ({mb:.2f} MB)")

    print("thin_map_layers.py complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
