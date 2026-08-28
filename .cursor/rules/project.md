# RedZone DSS — Cursor Project Rules

## Project

SIH 2026 Problem Statement 26191.

Deadline: 5 September 2026.

## Locked Geography

Rudraprayag district, Uttarakhand.

Do not add another district.

## Locked Hazards

1. Landslide
2. Cloudburst / flash-flood susceptibility

Do not add a third hazard.

## Technology

Frontend:
- React
- Vite
- TypeScript
- Leaflet
- react-leaflet

Backend:
- Python 3.11
- FastAPI

GIS:
- GeoPandas
- Rasterio
- Shapely
- PyProj
- NumPy

Storage:
- GeoJSON / JSON
- SQLite only if genuinely necessary

## Forbidden MVP Technology

Do NOT introduce:

- PostGIS
- GeoServer
- Kubernetes
- Redis
- Kafka
- GraphQL
- Microservices
- Authentication
- Mobile application
- Cesium
- OR-Tools
- OSRM
- Deep learning
- LLM chatbot

## Architecture

Precompute expensive GIS operations.

Runtime should primarily:
- load processed artifacts
- serve APIs
- render the dashboard

Frontend must have a static-data fallback.

## Data Integrity

Never represent derived model scores as official government hazard zonation.

Never represent estimated carrying capacity as statutory/legal capacity.

Synthetic data must always be explicitly labelled.

## Development

Inspect existing code before modifying anything.

Do not rewrite working code unnecessarily.

Do not add dependencies without justification.

Do not change mathematical formulas without explicitly explaining why.

Do not implement features outside the MVP without approval.

Working prototype > perfect architecture.