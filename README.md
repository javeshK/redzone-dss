# RedZone DSS

**SIH 2026 — Problem Statement 26191**

Intelligent Identification of Hazard-Based Red Zones, Carrying Capacity Assessment, and Immediate Relocation Needs for Vulnerable Habitations.

> AI-assisted, explainable GIS decision-support prototype for Rudraprayag district, Uttarakhand.

## Locked MVP Scope

- **Geography:** Rudraprayag district only
- **Hazards:** Landslide + Cloudburst / flash-flood susceptibility
- **Phase 2:** Real/derived open data, operational refresh, scenario slider, alerts, PDF, Hindi i18n
- **ML disabled** (`ml_enabled: false`) — see Phase 3 scaffold in `scripts/ml/`

## Phase 2 Quick Start

### Download open data

```bash
cd scripts
pip install -r requirements.txt
python download_data.py
```

### Run full pipeline (rainfall fetch → 01–05 → alerts → PDF)

```bash
python scripts/07_run_pipeline.py
```

### Schedule nightly refresh

```bash
# cron / Task Scheduler
python scripts/07_run_pipeline.py
```

Refresh status: `GET /api/meta/refresh-status`  
Dev refresh: `POST /api/admin/refresh`

## Quick Start (original)

### Prerequisites

- Python 3.11+
- Node.js 18+

### 1. GIS Pipeline (offline batch)

```bash
cd scripts
pip install -r requirements.txt
python 01_preprocess.py
python 02_risk_engine.py
python 03_vuln_engine.py
python 04_relocation.py
python 05_export.py
```

### 2. Backend API

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Dashboard

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### 4. Validate & Test (pre-demo)

```bash
# Sync artifacts and write export_manifest.json
cd scripts
python 05_export.py

# Offline artifact checks (25 habitations, 8+ sites, recommendations, parity)
python validate_demo.py

# API + scoring tests
cd ../backend
pytest tests/ -v
```

### 5. Fully Offline Demo (no API)

```bash
cd frontend
npm run build
npm run preview
```

Open http://localhost:4173 — the dashboard serves precomputed artifacts from `public/data/` with static fallback banners.

### 5. Demo freeze rehearsal (Day 9)

```bash
# Full automated rehearsal: export, validate, test, build, snapshots, backup
python scripts/run_demo_rehearsal.py

# Manual ×3 run-throughs
# See docs/REHEARSAL_CHECKLIST.md and docs/demo_script.md
```

**Phase 2 active** — see [`docs/FEATURE_FREEZE.md`](docs/FEATURE_FREEZE.md) for roadmap.

## Demo Flow

1. **Overview** — KPIs, data sources, limitations
2. **Risk Map** — District, red zones, landslides, streams, habitations, sites
3. **Habitation Panel** — Click a settlement → hazard, vulnerability, priority, explanation
4. **Relocation Planner** — Recommended site, capacity, reasons, runner-up

## Offline / Static Fallback

If the API is unavailable, the frontend loads precomputed artifacts from `frontend/public/data/`.
Run `05_export.py` to sync `out/` → `frontend/public/data/` and write `export_manifest.json` (checksums + parity check).

**Troubleshooting**

| Symptom | Fix |
|---------|-----|
| Blank map / 404 on `/data/*` | Run `python scripts/05_export.py` |
| API mode but empty layers | Ensure `out/` exists; restart `uvicorn` |
| `validate_demo.py` parity failure | Re-run `05_export.py` to re-sync |
| Synthetic/degraded banners | Expected when DEM or rainfall rasters are missing |
| Stale recommendations | Re-run full pipeline (`01`–`05`) |

## Important Disclaimers

- Derived hazard scores are **not** official government hazard zonation.
- Capacity is **first-order physical screening capacity**, not statutory or legally approved settlement capacity.
- Synthetic or expert-screened data is flagged in `meta.json` and the UI.

## Repository Layout

```text
config/          # weights.yaml, paths.yaml
data/            # raw + processed GIS inputs
out/             # precomputed GeoJSON + JSON artifacts
scripts/         # offline GIS pipeline (01–09, download, ML scaffold)
backend/         # FastAPI read-only API
frontend/        # React + Vite + Leaflet dashboard
docs/            # full specification
```

## Specification

Full implementation spec: [`docs/PS26191_SPEC.md`](docs/PS26191_SPEC.md)

Demo script: [`docs/demo_script.md`](docs/demo_script.md)

Rehearsal checklist: [`docs/REHEARSAL_CHECKLIST.md`](docs/REHEARSAL_CHECKLIST.md)

Feature freeze: [`docs/FEATURE_FREEZE.md`](docs/FEATURE_FREEZE.md)

## Mathematical Contracts

| Model | Formula |
|-------|---------|
| Landslide hazard | H_ls = 0.45·S + 0.40·L + 0.15·R |
| Flash-flood hazard | H_ff = 0.50·W + 0.50·R |
| Multi-hazard | H = 1 − (1−H_ls)(1−H_ff) |
| Vulnerability | V = weighted sum (renormalized if factors missing) |
| Priority | P = 0.60·H_hab + 0.40·V |
| Capacity | A_safe / 80 × access deraters |
| Site suitability | U_ij = weighted sum of safety, distance, access, capacity_fit |

All weights in [`config/weights.yaml`](config/weights.yaml).
