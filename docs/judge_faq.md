# Judge FAQ — RedZone DSS

## Is this using AI / machine learning?

No trained neural network in the current demo. Intelligence comes from automated GIS overlays, multi-criteria hazard scoring, vulnerability weighting, and explainable site ranking. A **Phase 3 hybrid ML scaffold** exists (`ml_enabled: false`) but is disabled until labelled events and backtest metrics pass gates.

## Are these official hazard zones?

No. Derived scores are decision-support indicators labeled `DERIVED` in metadata. They are not statutory or official government hazard zonation.

## What is "carrying capacity"?

First-order physical screening capacity based on buildable area, slope, hazard, and access deraters. It is **not** legally approved or statutory settlement capacity.

## Why Rudraprayag only?

MVP scope is locked to one district and two hazards (landslide + flash-flood) for a working demo. Multi-district parameterization is scaffolded behind an experimental flag.

## What data sources are used?

Open data: GSI landslide inventory (or steep-slope proxy), OSM waterways/roads via Overpass, SRTM/Copernicus DEM (or terrain-derived from district bbox), orographic rainfall from DEM, DataMeet village boundaries. Expert-screened demo habitations augmented by village polygon joins.

## What if live downloads fail?

`download_data.py` generates **terrain-derived** DEM and **orographic** rainfall patterns (not uniform synthetic). Provenance is documented in `download_manifest.json` and `meta.json` with `DERIVED` labels.

## Can this run offline?

Yes. Precomputed GeoJSON in `frontend/public/data/` enables full dashboard operation without the API.

## How are maps updated operationally?

`scripts/07_run_pipeline.py` orchestrates rainfall fetch → pipeline 01–05 → alerts → PDF export. Schedule nightly via cron/Task Scheduler. API exposes `GET /api/meta/refresh-status` and `POST /api/admin/refresh` (dev/demo).

## What is the rainfall scenario slider?

`GET /api/scenario/rainfall?factor=1.0|1.2|1.5` re-scores hazard from cached rasters with scaled rainfall. The UI slider shows a banner: scenario mode for decision-support exploration, **not a forecast**.

## What are the alerts?

Rule-based explainable alerts (`08_alerts.py`) when H_ff, H_hab, or pct_red exceed thresholds. Each alert includes human-readable reason strings.

## How are relocation sites chosen?

Sites pass hazard (<0.40), slope (<20°), protected-area exclusion, and minimum area (3 ha) filters. Ranked by U_ij suitability score with capacity constraint (C_available ≥ 0.5 × population).

## What is the Immediate override?

Priority forced to Immediate when ≥40% of habitation area is in red zone OR habitation hazard H_hab ≥ 0.80.

## Is Hindi supported?

Yes — bilingual nav, priority labels, disclaimer footer, and key map labels via a lightweight i18n dictionary (toggle हिं/EN in header).
