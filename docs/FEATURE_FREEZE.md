# RedZone DSS — Roadmap & Feature Status

**Updated:** 28 August 2026 — Phase 2 lift

## Phase 1 MVP (frozen baseline)

The Day-9 demo MVP remains the locked baseline: MCA pipeline, API, dashboard, static fallback, 25 habitations, 11 sites.

## Phase 2 — Lifted freeze (active)

| Phase | Status | Deliverables |
|-------|--------|--------------|
| **2A Authenticity** | Complete | `download_data.py` expanded; terrain-derived DEM + orographic rainfall; GSI proxy; OSM Overpass; village polygons; `data_layers` hashes in meta |
| **2B Operational refresh** | Complete | `06_fetch_rainfall.py`, `07_run_pipeline.py`, `run_log.json`, refresh API, Last updated UI |
| **2C SDMA features** | Complete | Rainfall scenario slider, rule-based alerts, PDF export, Hindi i18n, village polygon join |
| **2D Gated** | Foundation | Live weather overlay stub (disabled), district parameterization scaffold — behind `config/features.yaml` flags |
| **Phase 3 ML** | Scaffold only | `events/` template, `train_susceptibility.py` stub, `ml_enabled: false`, `ml_metrics.json` placeholder |

## Guardrails (unchanged)

- Do **not** claim official government hazard zonation
- Do **not** change core MCA formulas in `config/weights.yaml` without documentation
- Keep static fallback architecture
- Keep explainable MCA — no black-box ML in UI until backtest gates pass

## Verification

```bash
python scripts/download_data.py
python scripts/07_run_pipeline.py
python scripts/run_demo_rehearsal.py
cd backend && pytest tests/ -v
```

## Scheduling (production)

Nightly refresh via Windows Task Scheduler or cron:

```bash
python scripts/07_run_pipeline.py
```

## Not in scope (Tier 3)

- Official statutory carrying capacity claims
- Live satellite inference in demo loop
- 7-day cloudburst prediction without labelled events + backtest
- Microservices, PostGIS, Kafka, GraphQL
