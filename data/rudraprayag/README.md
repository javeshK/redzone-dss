# Data Directory — Rudraprayag

## Structure

```text
data/rudraprayag/
├── raw/          # Original downloads (gitignored if large)
├── processed/    # Clipped rasters, intermediate outputs (gitignored)
└── README.md     # This file
```

## Day-1 Download Checklist

1. [ ] Rudraprayag district polygon — [DataMeet maps](https://github.com/datameet/maps) → `raw/district.geojson`
2. [ ] Uttarakhand village boundaries — [DataMeet](https://projects.datameet.org/indian_village_boundaries/) → `raw/villages.geojson`
3. [ ] GSI landslide points — [bharatlas](https://bharatlas.com/view/gsi_landslide_inventory) → `raw/landslides.geojson`
4. [ ] DEM 30m — Copernicus GLO-30 or SRTM → `raw/dem/*.tif`
5. [ ] OSM extract — [Geofabrik](https://download.geofabrik.de/asia/india.html) → `raw/osm_waterways.geojson`, `raw/osm_roads.geojson`, `raw/osm_amenities.geojson`
6. [ ] WorldPop 100m — [HDX](https://data.humdata.org/dataset/worldpop-population-density-for-india) → `raw/worldpop.tif`
7. [ ] CHIRPS or ERA5 rainfall → `raw/rainfall.tif`
8. [ ] ESA WorldCover → `raw/worldcover.tif`
9. [ ] Protected areas (WDPA) → `raw/protected_areas.geojson`

## Processing

After downloads, run the pipeline from `scripts/`:

```bash
python 01_preprocess.py
python 02_risk_engine.py
python 03_vuln_engine.py
python 04_relocation.py
python 05_export.py
```

## Fallback Policy

If a primary source is unavailable, use the fallback matrix in `docs/PS26191_SPEC.md` §2.9.
Always label `SYNTHETIC` or `EXPERT_SCREENED` data in `out/meta.json` and the UI.

## CRS

- Display: EPSG:4326
- Compute (distances/areas): EPSG:32644
