# Data Directory — Rudraprayag

## Structure

```text
data/rudraprayag/
├── raw/          # Original downloads (gitignored if large)
├── processed/    # Clipped rasters, intermediate outputs (gitignored)
├── events/       # Phase 3 labelled events (template provided)
└── README.md     # This file
```

## Automated Download (Phase 2)

```bash
cd scripts
python download_data.py
```

This attempts live sources and falls back to documented derived data:

| Asset | Live source | Fallback |
|-------|-------------|----------|
| District | geoBoundaries ADM2 | Bbox |
| DEM | OpenTopography SRTM GL1 | Terrain-derived from bbox |
| Rainfall | CHIRPS/ERA5 | Orographic model from DEM |
| Landslides | GSI/bharatlas | Steep-slope proxy from DEM |
| OSM | Overpass API | Pipeline derives from TWI |
| Villages | DataMeet | Buffer polygons from demo points |

Download manifest: `raw/download_manifest.json`

## Full Pipeline

```bash
python scripts/07_run_pipeline.py
```

Or step-by-step:

```bash
python 06_fetch_rainfall.py
python 01_preprocess.py
python 02_risk_engine.py
python 03_vuln_engine.py
python 04_relocation.py
python 05_export.py
python 08_alerts.py
python 09_export_pdf.py
```

## Scheduling

Nightly refresh (Windows Task Scheduler / cron):

```bash
python scripts/07_run_pipeline.py
```

## Fallback Policy

If a primary source is unavailable, use the fallback matrix in `docs/PS26191_SPEC.md` §2.9.
Always label `DERIVED` or `EXPERT_SCREENED` data in `out/meta.json` and the UI.

## CRS

- Display: EPSG:4326
- Compute (distances/areas): EPSG:32644
