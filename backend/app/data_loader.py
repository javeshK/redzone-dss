"""Load precomputed artifacts from out/ at startup."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.schemas import (
    ExplainFactor,
    HabitationDetail,
    HabitationSummary,
    MetaResponse,
    RecommendationComparison,
    RecommendationResponse,
    SiteRecommendation,
    SiteSummary,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "out"


class DataStore:
    def __init__(self, out_dir: Path | None = None) -> None:
        self.out_dir = out_dir or OUT_DIR
        self._district: dict[str, Any] | None = None
        self._habitations: dict[str, Any] | None = None
        self._sites: dict[str, Any] | None = None
        self._layers: dict[str, dict[str, Any]] = {}
        self._meta: MetaResponse | None = None
        self._recommendations: dict[str, Any] = {}
        self._habitation_index: dict[str, dict[str, Any]] = {}
        self._loaded = False

    def load(self, force: bool = False) -> None:
        if self._loaded and not force:
            return
        self._district = self._read_geojson("district.geojson")
        self._habitations = self._read_geojson("habitations.geojson")
        self._sites = self._read_geojson("sites.geojson")
        for name in ("red_zones", "landslides", "streams"):
            self._layers[name] = self._read_geojson(f"{name}.geojson")
        meta_raw = self._read_json("meta.json")
        self._meta = MetaResponse(**meta_raw)
        rec_raw = self._read_json("recommendations.json")
        self._recommendations = rec_raw.get("recommendations", {})
        self._build_habitation_index()
        self._loaded = True

    def _read_json(self, filename: str) -> dict[str, Any]:
        path = self.out_dir / filename
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _read_geojson(self, filename: str) -> dict[str, Any]:
        path = self.out_dir / filename
        if not path.exists():
            return {"type": "FeatureCollection", "features": []}
        return json.loads(path.read_text(encoding="utf-8"))

    def _build_habitation_index(self) -> None:
        self._habitation_index = {}
        if not self._habitations:
            return
        for feat in self._habitations.get("features", []):
            props = feat.get("properties", {})
            hab_id = props.get("id")
            if hab_id:
                self._habitation_index[hab_id] = feat

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def get_meta(self) -> MetaResponse:
        self.load()
        assert self._meta is not None
        return self._meta

    def get_district_geojson(self) -> dict[str, Any]:
        self.load()
        return self._district or {"type": "FeatureCollection", "features": []}

    def get_district_bbox(self) -> list[float]:
        fc = self.get_district_geojson()
        coords: list[list[float]] = []
        for feat in fc.get("features", []):
            geom = feat.get("geometry", {})
            if geom.get("type") == "Polygon":
                for ring in geom.get("coordinates", []):
                    coords.extend(ring)
        if not coords:
            return [78.75, 30.05, 79.55, 30.75]
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        return [min(lons), min(lats), max(lons), max(lats)]

    def _feat_to_habitation_summary(self, feat: dict[str, Any]) -> HabitationSummary:
        props = feat["properties"]
        lon, lat = feat["geometry"]["coordinates"]
        return HabitationSummary(
            id=props["id"],
            name=props["name"],
            block=props.get("block", ""),
            pop=props["pop"],
            lat=lat,
            lon=lon,
            h_ls=props["h_ls"],
            h_ff=props["h_ff"],
            h=props["h"],
            v=props["v"],
            p=props["p"],
            priority=props["priority"],
            pct_red=props["pct_red"],
            zone_class=props.get("zone_class", "Yellow"),
            rec_site_id=props.get("rec_site_id"),
            rec_score=props.get("rec_score"),
            source=props.get("source", "EXPERT_SCREENED"),
            hazard_source=props.get("hazard_source"),
        )

    def list_habitations(self) -> list[HabitationSummary]:
        self.load()
        result = []
        for feat in (self._habitations or {}).get("features", []):
            result.append(self._feat_to_habitation_summary(feat))
        return result

    def get_habitation(self, hab_id: str) -> HabitationDetail | None:
        self.load()
        feat = self._habitation_index.get(hab_id)
        if not feat:
            return None
        props = feat["properties"]
        summary = self._feat_to_habitation_summary(feat)
        explain = [ExplainFactor(**e) for e in props.get("explain", [])]
        vuln_explain = [ExplainFactor(**e) for e in props.get("vuln_explain", [])]
        return HabitationDetail(
            **summary.model_dump(),
            explain=explain,
            vuln_explain=vuln_explain,
            why_site=props.get("why_site", []),
        )

    def get_habitations_geojson(self) -> dict[str, Any]:
        self.load()
        return self._habitations or {"type": "FeatureCollection", "features": []}

    def get_layer(self, name: str) -> dict[str, Any] | None:
        self.load()
        if name in self._layers:
            return self._layers[name]
        if name == "district":
            return self.get_district_geojson()
        if name == "habitations":
            return self.get_habitations_geojson()
        if name == "sites":
            return self._sites
        return None

    def list_sites(self) -> list[SiteSummary]:
        self.load()
        result = []
        for feat in (self._sites or {}).get("features", []):
            props = feat["properties"]
            lon, lat = feat["geometry"]["coordinates"]
            result.append(
                SiteSummary(
                    id=props["id"],
                    name=props["name"],
                    lat=lat,
                    lon=lon,
                    h_mean=props["h_mean"],
                    slope_mean_deg=props["slope_mean_deg"],
                    area_ha=props["area_ha"],
                    capacity=props["capacity"],
                    capacity_available=props["capacity_available"],
                    existing_population=props.get("existing_population", 0),
                    f_road=props["f_road"],
                    f_water=props["f_water"],
                    f_health=props["f_health"],
                    source=props.get("source", "EXPERT_SCREENED"),
                    screening_note=props.get(
                        "screening_note", "First-order physical screening capacity"
                    ),
                )
            )
        return result

    def get_recommendation(self, hab_id: str) -> RecommendationResponse | None:
        self.load()
        rec = self._recommendations.get(hab_id)
        if not rec:
            return None

        def _parse_site(data: dict) -> SiteRecommendation:
            explain = [ExplainFactor(**e) for e in data.get("explain", [])]
            return SiteRecommendation(
                **{k: v for k, v in data.items() if k != "explain"},
                explain=explain,
            )

        top = _parse_site(rec["top"])
        runner_up = _parse_site(rec["runner_up"]) if rec.get("runner_up") else None
        comparison = None
        if rec.get("comparison"):
            comparison = RecommendationComparison(**rec["comparison"])
        return RecommendationResponse(
            hab_id=rec["hab_id"],
            hab_name=rec["hab_name"],
            top=top,
            runner_up=runner_up,
            comparison=comparison,
        )


store = DataStore()
