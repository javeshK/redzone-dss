"""Enrich candidate sites with pipeline hazard/slope samples."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from _habitation_hazard import sample_raster_at_point


def enrich_site_from_rasters(site: dict, paths: dict, repo_root: Path) -> dict:
    """Override p_hazard and p_slope_lt15 from processed rasters when available."""
    enriched = dict(site)
    h_path = repo_root / paths["processed"]["hazard_raster"]
    slope_path = repo_root / paths["processed"]["slope"]

    h = sample_raster_at_point(h_path, site["lon"], site["lat"])
    if h is not None:
        enriched["p_hazard"] = round(h, 4)
        enriched["hazard_source"] = "PIPELINE"
    else:
        enriched["hazard_source"] = "EXPERT_SCREENED"

    if slope_path.exists():
        try:
            import rasterio
            from pyproj import Transformer

            from _crs import DISPLAY_CRS

            with rasterio.open(slope_path) as src:
                transformer = Transformer.from_crs(DISPLAY_CRS, src.crs, always_xy=True)
                x, y = transformer.transform(site["lon"], site["lat"])
                row, col = src.index(x, y)
                if 0 <= row < src.height and 0 <= col < src.width:
                    slope_deg = float(src.read(1)[row, col])
                    if slope_deg != src.nodata:
                        enriched["slope_mean_deg"] = round(slope_deg, 1)
                        enriched["p_slope_lt15"] = round(
                            float(np.clip(1.0 - (slope_deg - 5.0) / 25.0, 0.3, 0.95)), 4
                        )
        except Exception:
            pass

    if "slope_mean_deg" not in enriched:
        enriched["slope_mean_deg"] = round((1 - enriched["p_slope_lt15"]) * 30, 1)

    return enriched
