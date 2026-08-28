# Judge FAQ — RedZone DSS

## Is this using AI / machine learning?

No trained neural network. Intelligence comes from automated GIS overlays, multi-criteria hazard scoring, vulnerability weighting, and explainable site ranking.

## Are these official hazard zones?

No. Derived scores are decision-support indicators labeled `DERIVED` in metadata. They are not statutory or official government hazard zonation.

## What is "carrying capacity"?

First-order physical screening capacity based on buildable area, slope, hazard, and access deraters. It is **not** legally approved or statutory settlement capacity.

## Why Rudraprayag only?

MVP scope is locked to one district and two hazards (landslide + flash-flood) for a working demo within the hackathon timeline.

## What data sources are used?

Open data: GSI landslide inventory, OSM waterways/roads, Copernicus/SRTM DEM, DataMeet boundaries. Expert-screened demo habitations and candidate sites where village joins are incomplete.

## What if data is missing?

Fallback matrix in the spec: synthetic proxies are used with explicit `SYNTHETIC` or `EXPERT_SCREENED` labels in UI and `meta.json`.

## Can this run offline?

Yes. Precomputed GeoJSON in `frontend/public/data/` enables full dashboard operation without the API.

## How are relocation sites chosen?

Sites pass hazard (<0.40), slope (<20°), protected-area exclusion, and minimum area (3 ha) filters. Ranked by U_ij suitability score with capacity constraint (C_available ≥ 0.5 × population).

## What is the Immediate override?

Priority forced to Immediate when ≥40% of habitation area is in red zone OR habitation hazard H_hab ≥ 0.80.
