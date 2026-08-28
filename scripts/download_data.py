"""Download helper — fetch open datasets for Rudraprayag."""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import REPO_ROOT, ensure_dirs, load_paths

# geoBoundaries simplified India ADM2 — filter for Rudraprayag
GEOBOUNDARIES_URL = (
    "https://github.com/wmgeolab/geoBoundaries/raw/94651f77"
    "/releaseData/gbOpen/IND/ADM2/geoBoundaries-IND-ADM2.geojson"
)


def download_district_fallback():
    """Attempt to download district boundary; fall back to bbox if unavailable."""
    paths = load_paths()
    raw_dir = REPO_ROOT / paths["raw_dir"]
    ensure_dirs(raw_dir)
    out_path = REPO_ROOT / paths["raw"]["district"]

    try:
        print(f"Downloading geoBoundaries ADM2...")
        with urllib.request.urlopen(GEOBOUNDARIES_URL, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        features = [
            f for f in data.get("features", [])
            if "Rudraprayag" in str(f.get("properties", {}))
        ]
        if features:
            fc = {"type": "FeatureCollection", "features": features}
            out_path.write_text(json.dumps(fc), encoding="utf-8")
            print(f"  Saved {len(features)} feature(s) to {out_path}")
            return True
    except Exception as e:
        print(f"  [warn] Download failed: {e}")

    # Bbox fallback
    bbox = paths["bbox"]
    fc = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {"name": "Rudraprayag", "state": "Uttarakhand", "source": "BBOX_FALLBACK"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [bbox["min_lon"], bbox["min_lat"]],
                    [bbox["max_lon"], bbox["min_lat"]],
                    [bbox["max_lon"], bbox["max_lat"]],
                    [bbox["min_lon"], bbox["max_lat"]],
                    [bbox["min_lon"], bbox["min_lat"]],
                ]],
            },
        }],
    }
    out_path.write_text(json.dumps(fc, indent=2), encoding="utf-8")
    print(f"  Wrote bbox fallback to {out_path}")
    return False


def main():
    paths = load_paths()
    ensure_dirs(
        REPO_ROOT / paths["raw_dir"],
        REPO_ROOT / paths["processed_dir"],
    )
    print("RedZone DSS — Data Download Helper")
    print("=" * 40)
    download_district_fallback()
    print()
    print("Manual downloads still required:")
    print("  - DEM: Copernicus GLO-30 or SRTM -> data/rudraprayag/raw/dem/")
    print("  - GSI landslides: bharatlas -> data/rudraprayag/raw/landslides.geojson")
    print("  - OSM: Geofabrik -> data/rudraprayag/raw/osm_*.geojson")
    print("See data/rudraprayag/README.md for full checklist.")


if __name__ == "__main__":
    main()
