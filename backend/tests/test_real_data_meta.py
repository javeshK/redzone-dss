"""Phase 2 tests — meta flags when real/derived data present."""

from pathlib import Path
import json

REPO_ROOT = Path(__file__).resolve().parents[2]
META_PATH = REPO_ROOT / "out" / "meta.json"


def test_meta_has_audit_fields():
    assert META_PATH.exists(), "meta.json missing — run pipeline first"
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    assert "data_as_of" in meta
    assert "pipeline_version" in meta
    assert "data_layers" in meta


def test_synthetic_flags_cleared_when_data_present():
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    raw_dem = REPO_ROOT / "data" / "rudraprayag" / "raw" / "dem"
    raw_rain = REPO_ROOT / "data" / "rudraprayag" / "raw" / "rainfall.tif"
    if list(raw_dem.glob("*.tif")) and raw_rain.exists():
        assert meta["synthetic_data_used"] is False, "synthetic flag should clear when DEM+rainfall exist"
        assert meta["degraded_mode"] is False, "degraded flag should clear when rainfall exists"


def test_dem_source_not_uniform_synthetic():
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))
    dem_sources = [s for s in meta.get("sources", []) if s.get("layer") == "dem"]
    if dem_sources:
        prov = dem_sources[0].get("provenance")
        assert prov in ("OPEN_DATA", "DERIVED"), f"DEM should be OPEN_DATA or DERIVED, got {prov}"
