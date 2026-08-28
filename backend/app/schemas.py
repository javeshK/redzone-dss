"""Pydantic schemas — shared JSON contract for RedZone DSS API."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


PriorityClass = Literal["Immediate", "Short-term", "Medium-term", "Monitor"]
ZoneClass = Literal["Red", "Orange", "Yellow", "Green"]
Provenance = Literal["OFFICIAL", "OPEN_DATA", "DERIVED", "EXPERT_SCREENED", "SYNTHETIC"]


class ExplainFactor(BaseModel):
    factor: str
    value: float
    weight: float
    contribution: float
    note: str | None = None


class HabitationSummary(BaseModel):
    id: str
    name: str
    block: str
    pop: int
    lat: float
    lon: float
    h_ls: float
    h_ff: float
    h: float
    v: float
    p: float
    priority: PriorityClass
    pct_red: float
    zone_class: ZoneClass
    rec_site_id: str | None = None
    rec_score: float | None = None
    source: Provenance = "EXPERT_SCREENED"
    hazard_source: str | None = None


class HabitationDetail(HabitationSummary):
    explain: list[ExplainFactor] = Field(default_factory=list)
    vuln_explain: list[ExplainFactor] = Field(default_factory=list)
    why_site: list[str] = Field(default_factory=list)


class SiteSummary(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    h_mean: float
    slope_mean_deg: float
    area_ha: float
    capacity: int
    capacity_available: int
    existing_population: int
    f_road: float
    f_water: float
    f_health: float
    source: Provenance = "EXPERT_SCREENED"
    screening_note: str = "First-order physical screening capacity"


class SiteRecommendation(BaseModel):
    site_id: str
    site_name: str
    score: float
    safety: float
    distance_km: float
    road_access: float
    healthcare_access: float
    water_access: float
    school_access: float
    capacity: int
    capacity_available: int
    reasons: list[str]
    explain: list[ExplainFactor] = Field(default_factory=list)
    meets_capacity_threshold: bool = True


class RecommendationComparison(BaseModel):
    score_delta: float
    distance_delta_km: float
    capacity_delta: int
    notes: list[str] = Field(default_factory=list)


class RecommendationResponse(BaseModel):
    hab_id: str
    hab_name: str
    top: SiteRecommendation
    runner_up: SiteRecommendation | None = None
    comparison: RecommendationComparison | None = None


class SourceMeta(BaseModel):
    layer: str
    provenance: Provenance
    url: str | None = None
    note: str | None = None


class Kpis(BaseModel):
    habitation_count: int = 0
    immediate_count: int = 0
    short_term_count: int = 0
    medium_term_count: int = 0
    monitor_count: int = 0
    site_count: int = 0
    red_zone_area_ha: float = 0.0
    district_area_ha: float = 0.0


class MetaResponse(BaseModel):
    district: str
    generated_at: str
    model_version: str
    weights_version: str
    degraded_mode: bool = False
    synthetic_data_used: bool = False
    sources: list[SourceMeta] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    kpis: Kpis = Field(default_factory=Kpis)


class DistrictResponse(BaseModel):
    name: str
    state: str
    district_code: str
    bbox: list[float]
    geojson: dict[str, Any]
    meta: MetaResponse


class HealthResponse(BaseModel):
    status: str = "ok"
    district: str
    model_version: str
    data_loaded: bool
