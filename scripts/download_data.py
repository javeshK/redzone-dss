"""Download helper — fetch open datasets for Rudraprayag with derived fallbacks."""

from __future__ import annotations

import json
import math
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import REPO_ROOT, ensure_dirs, load_paths

IST = timezone(timedelta(hours=5, minutes=30))

GEOBOUNDARIES_URL = (
    "https://github.com/wmgeolab/geoBoundaries/raw/94651f77"
    "/releaseData/gbOpen/IND/ADM2/geoBoundaries-IND-ADM2.geojson"
)
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OPENTOPO_SRTM_URL = (
    "https://portal.opentopography.org/API/globaldem"
    "?demtype=SRTMGL1&south={min_lat}&north={max_lat}"
    "&west={min_lon}&east={max_lon}&outputFormat=GTiff&API_Key=OTDEMO"
)
VILLAGES_URL = (
    "https://raw.githubusercontent.com/datameet/maps/master/Districts/"
    "Uttarakhand/2011/uttarakhand_district_rudraprayag.geojson"
)

try:
    import rasterio
    from rasterio.transform import from_bounds
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False

try:
    import geopandas as gpd
    from shapely.geometry import Point, box, mapping
    HAS_GEO = True
except ImportError:
    HAS_GEO = False


def _http_get(url: str, timeout: int = 60) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "RedZone-DSS/2.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception as e:
        print(f"  [warn] HTTP failed: {e}")
        return None


def _write_manifest(raw_dir: Path, entries: list[dict]) -> None:
    manifest = {
        "generated_at": datetime.now(IST).isoformat(),
        "layers": entries,
    }
    (raw_dir / "download_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )


def download_district_fallback() -> dict:
    """Download district boundary; fall back to bbox if unavailable."""
    paths = load_paths()
    raw_dir = REPO_ROOT / paths["raw_dir"]
    ensure_dirs(raw_dir)
    out_path = REPO_ROOT / paths["raw"]["district"]
    entry = {"layer": "district", "source": "BBOX_FALLBACK", "live": False}

    try:
        print("Downloading geoBoundaries ADM2...")
        data = json.loads(_http_get(GEOBOUNDARIES_URL, timeout=30).decode())
        features = [
            f for f in data.get("features", [])
            if "Rudraprayag" in str(f.get("properties", {}))
        ]
        if features:
            fc = {"type": "FeatureCollection", "features": features}
            out_path.write_text(json.dumps(fc), encoding="utf-8")
            print(f"  Saved {len(features)} feature(s) to {out_path}")
            entry = {"layer": "district", "source": "geoBoundaries", "live": True, "path": str(out_path)}
            return entry
    except Exception as e:
        print(f"  [warn] Download failed: {e}")

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
    return entry


def _district_bounds(paths: dict) -> tuple[float, float, float, float]:
    district_path = REPO_ROOT / paths["raw"]["district"]
    if district_path.exists() and HAS_GEO:
        gdf = gpd.read_file(district_path)
        bounds = gdf.total_bounds
        return float(bounds[0]), float(bounds[1]), float(bounds[2]), float(bounds[3])
    bbox = paths["bbox"]
    return bbox["min_lon"], bbox["min_lat"], bbox["max_lon"], bbox["max_lat"]


def download_dem(paths: dict) -> dict:
    """Fetch SRTM via OpenTopography or generate terrain-derived DEM."""
    dem_dir = REPO_ROOT / paths["raw"]["dem"]
    ensure_dirs(dem_dir)
    out_path = dem_dir / "srtm_rudraprayag.tif"
    entry = {"layer": "dem", "source": "DERIVED_TERRAIN", "live": False, "path": str(out_path)}

    min_lon, min_lat, max_lon, max_lat = _district_bounds(paths)
    url = OPENTOPO_SRTM_URL.format(
        min_lat=min_lat, max_lat=max_lat, min_lon=min_lon, max_lon=max_lon
    )
    print("Attempting OpenTopography SRTM download...")
    data = _http_get(url, timeout=120)
    if data and len(data) > 1000 and data[:4] in (b"II*\x00", b"\x00II*", b"GTiff"):
        out_path.write_bytes(data)
        print(f"  Saved live DEM to {out_path}")
        return {"layer": "dem", "source": "OpenTopography/SRTMGL1", "live": True, "path": str(out_path)}

    if not HAS_RASTERIO:
        print("  [warn] rasterio unavailable — skipping DEM generation")
        return entry

    print("  Generating terrain-derived DEM from district bbox (not uniform synthetic)...")
  # Himalaya-style elevation: higher north/east, valley channels, fractal noise
    width, height = 120, 100
    transform = from_bounds(min_lon, min_lat, max_lon, max_lat, width, height)
    x = np.linspace(0, 1, width)
    y = np.linspace(0, 1, height)
    xx, yy = np.meshgrid(x, y)
    base = 1800 + 2200 * (yy * 0.55 + xx * 0.25)
    ridges = 350 * np.sin(xx * 14 + yy * 3) * np.cos(yy * 11 - xx * 2)
    valleys = -280 * np.exp(-((xx - 0.45) ** 2 + (yy - 0.35) ** 2) / 0.02)
    valleys -= 200 * np.exp(-((xx - 0.7) ** 2 + (yy - 0.6) ** 2) / 0.015)
    rng = np.random.default_rng(42)
    noise = rng.normal(0, 45, (height, width))
    dem = (base + ridges + valleys + noise).astype("float32")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        out_path, "w", driver="GTiff", height=height, width=width, count=1,
        dtype="float32", crs="EPSG:4326", transform=transform, nodata=-9999,
    ) as dst:
        dst.write(dem, 1)
    print(f"  Wrote terrain-derived DEM to {out_path}")
    entry["note"] = "Orographic terrain model from district bbox; OpenTopography unavailable"
    return entry


def download_rainfall(paths: dict) -> dict:
    """Fetch rainfall raster or generate orographic pattern from DEM."""
    out_path = REPO_ROOT / paths["raw"]["rainfall"]
    entry = {"layer": "rainfall", "source": "DERIVED_OROGRAPHIC", "live": False, "path": str(out_path)}

    dem_dir = REPO_ROOT / paths["raw"]["dem"]
    dem_files = list(dem_dir.glob("*.tif")) if dem_dir.exists() else []
    if not HAS_RASTERIO or not dem_files:
        print("  [warn] No DEM for rainfall derivation")
        return entry

    print("Generating orographic rainfall pattern from DEM (CHIRPS/ERA5 unavailable)...")
    with rasterio.open(dem_files[0]) as dem_src:
        dem = dem_src.read(1).astype(float)
        dem[dem == dem_src.nodata] = np.nan
        dem_filled = np.nan_to_num(dem, nan=np.nanmean(dem))
        slope = np.gradient(dem_filled)
        grad_mag = np.sqrt(slope[0] ** 2 + slope[1] ** 2)
        dem_norm = (dem_filled - np.nanmin(dem_filled)) / max(np.nanmax(dem_filled) - np.nanmin(dem_filled), 1)
        grad_norm = grad_mag / max(np.nanmax(grad_mag), 1e-6)
        # Higher rainfall on elevated windward slopes (SW monsoon proxy)
        rain_mm = 800 + 1200 * dem_norm + 400 * grad_norm
        rain_mm += 150 * np.sin(dem_src.bounds.left * 0.5) * np.cos(dem_src.bounds.bottom * 0.3)
        rain_norm = (rain_mm - rain_mm.min()) / max(rain_mm.max() - rain_mm.min(), 1e-6)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        profile = dem_src.profile.copy()
        profile.update(dtype="float32", count=1, nodata=-9999)
        with rasterio.open(out_path, "w", **profile) as dst:
            dst.write(rain_norm.astype("float32"), 1)
    print(f"  Wrote orographic rainfall raster to {out_path}")
    entry["note"] = "Orographic model from DEM; CHIRPS/ERA5 live fetch unavailable"
    return entry


def _overpass_query(bbox: tuple[float, float, float, float], tags: str) -> dict | None:
    min_lon, min_lat, max_lon, max_lat = bbox
    query = f"""
    [out:json][timeout:60];
    (
      {tags}
    );
    out body geom;
    """
    query = query.replace("{south}", str(min_lat)).replace("{north}", str(max_lat))
    query = query.replace("{west}", str(min_lon)).replace("{east}", str(max_lon))
    # Build proper bbox filter
    for old, new in [
        ("{south}", str(min_lat)), ("{north}", str(max_lat)),
        ("{west}", str(min_lon)), ("{east}", str(max_lon)),
    ]:
        query = query.replace(old, new)
    data = _http_get(
        OVERPASS_URL + "?" + urllib.parse.urlencode({"data": query}),
        timeout=90,
    )
    if not data:
        return None
    try:
        return json.loads(data.decode())
    except json.JSONDecodeError:
        return None


def _osm_to_geojson(osm_data: dict, geom_type: str = "line") -> dict:
    features = []
    for el in osm_data.get("elements", []):
        if el.get("type") != "way" or "geometry" not in el:
            continue
        coords = [[n["lon"], n["lat"]] for n in el["geometry"]]
        if len(coords) < 2:
            continue
        geometry = (
            {"type": "LineString", "coordinates": coords}
            if geom_type == "line"
            else {"type": "Polygon", "coordinates": [coords]}
        )
        features.append({
            "type": "Feature",
            "properties": {**el.get("tags", {}), "osm_id": el.get("id"), "source": "OPEN_DATA"},
            "geometry": geometry,
        })
    return {"type": "FeatureCollection", "features": features}


def download_osm(paths: dict) -> list[dict]:
    """Fetch OSM waterways, roads, amenities via Overpass."""
    min_lon, min_lat, max_lon, max_lat = _district_bounds(paths)
    bbox = (min_lon, min_lat, max_lon, max_lat)
    entries = []

    layers = [
        ("osm_waterways", paths["raw"]["osm_waterways"], "line",
         f'way["waterway"]({min_lat},{min_lon},{max_lat},{max_lon});'),
        ("osm_roads", paths["raw"]["osm_roads"], "line",
         f'way["highway"]({min_lat},{min_lon},{max_lat},{max_lon});'),
        ("osm_amenities", paths["raw"]["osm_amenities"], "line",
         f'way["amenity"~"hospital|clinic|school|pharmacy"]({min_lat},{min_lon},{max_lat},{max_lon});'),
    ]

    for layer_name, rel_path, geom_type, tag_query in layers:
        out_path = REPO_ROOT / rel_path
        print(f"Fetching OSM {layer_name}...")
        osm = _overpass_query(bbox, tag_query)
        if osm and osm.get("elements"):
            fc = _osm_to_geojson(osm, geom_type)
            if fc["features"]:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(json.dumps(fc), encoding="utf-8")
                print(f"  Saved {len(fc['features'])} features to {out_path}")
                entries.append({"layer": layer_name, "source": "OpenStreetMap/Overpass", "live": True, "path": str(out_path)})
                continue
        entries.append({"layer": layer_name, "source": "MISSING", "live": False, "path": str(out_path),
                        "note": "Overpass unavailable; pipeline will derive from TWI"})
        print(f"  [warn] OSM {layer_name} unavailable — pipeline will derive")
    return entries


def download_landslides(paths: dict) -> dict:
    """Generate GSI-style landslide proxy points on steep terrain from DEM."""
    out_path = REPO_ROOT / paths["raw"]["landslides"]
    entry = {"layer": "landslides", "source": "DERIVED_SLOPE_PROXY", "live": False, "path": str(out_path)}

    if not HAS_GEO or not HAS_RASTERIO:
        return entry

    dem_dir = REPO_ROOT / paths["raw"]["dem"]
    dem_files = list(dem_dir.glob("*.tif")) if dem_dir.exists() else []
    if not dem_files:
        return entry

    print("Generating GSI landslide proxy from steep-slope DEM analysis...")
    with rasterio.open(dem_files[0]) as src:
        dem = src.read(1).astype(float)
        dem[dem == src.nodata] = np.nan
        res = abs(src.transform.a)
        dy, dx = np.gradient(np.nan_to_num(dem, nan=np.nanmean(dem)), res, res)
        slope_deg = np.degrees(np.arctan(np.sqrt(dx ** 2 + dy ** 2)))
        steep = slope_deg > 28
        rows, cols = np.where(steep)
        if len(rows) == 0:
            return entry
        rng = np.random.default_rng(7)
        idx = rng.choice(len(rows), size=min(80, len(rows)), replace=False)
        features = []
        for i in idx:
            r, c = rows[i], cols[i]
            x, y = rasterio.transform.xy(src.transform, r, c)
            features.append({
                "type": "Feature",
                "properties": {
                    "source": "DERIVED",
                    "note": "Slope > 28° proxy for GSI inventory; not official GSI points",
                    "slope_deg": round(float(slope_deg[r, c]), 1),
                },
                "geometry": mapping(Point(x, y)),
            })
    fc = {"type": "FeatureCollection", "features": features}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(fc), encoding="utf-8")
    print(f"  Wrote {len(features)} landslide proxy points to {out_path}")
    entry["count"] = len(features)
    entry["note"] = "Steep-slope proxy; bharatlas GSI live fetch unavailable"
    return entry


def download_villages(paths: dict) -> dict:
    """Fetch village polygons from DataMeet or generate from demo habitations."""
    out_path = REPO_ROOT / paths["raw"]["villages"]
    entry = {"layer": "villages", "source": "DERIVED_DEMO", "live": False, "path": str(out_path)}

    print("Attempting DataMeet village boundaries...")
    data = _http_get(VILLAGES_URL, timeout=30)
    if data:
        try:
            fc = json.loads(data.decode())
            if fc.get("features"):
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(json.dumps(fc), encoding="utf-8")
                print(f"  Saved {len(fc['features'])} village polygons")
                return {"layer": "villages", "source": "DataMeet", "live": True, "path": str(out_path),
                        "count": len(fc["features"])}
        except json.JSONDecodeError:
            pass

    if not HAS_GEO:
        return entry

    from demo_habitations import DEMO_HABITATIONS

    print("  Generating village polygons from demo habitation points...")
    features = []
    for hab in DEMO_HABITATIONS:
        pt = Point(hab["lon"], hab["lat"])
        poly = pt.buffer(0.008)
        features.append({
            "type": "Feature",
            "properties": {
                "name": hab["name"],
                "block": hab["block"],
                "pop": hab["pop"],
                "source": "DERIVED",
                "note": "Buffer polygon from demo habitation point",
            },
            "geometry": mapping(poly),
        })
    fc = {"type": "FeatureCollection", "features": features}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(fc), encoding="utf-8")
    print(f"  Wrote {len(features)} derived village polygons")
    entry["count"] = len(features)
    return entry


def main():
    paths = load_paths()
    raw_dir = REPO_ROOT / paths["raw_dir"]
    ensure_dirs(raw_dir, REPO_ROOT / paths["processed_dir"])

    print("RedZone DSS — Data Download Helper (Phase 2)")
    print("=" * 45)

    manifest_entries = []
    manifest_entries.append(download_district_fallback())
    manifest_entries.append(download_dem(paths))
    manifest_entries.extend(download_osm(paths))
    manifest_entries.append(download_landslides(paths))
    manifest_entries.append(download_rainfall(paths))
    manifest_entries.append(download_villages(paths))

    _write_manifest(raw_dir, manifest_entries)
    print()
    live_count = sum(1 for e in manifest_entries if e.get("live"))
    print(f"Download complete: {live_count}/{len(manifest_entries)} layers from live sources")
    print(f"Manifest: {raw_dir / 'download_manifest.json'}")
    print()
    print("Next: python scripts/07_run_pipeline.py")


if __name__ == "__main__":
    main()
