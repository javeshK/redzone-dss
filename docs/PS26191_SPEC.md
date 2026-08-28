# PS 26191 — Smart India Hackathon 2026  
## 10-Day Working Prototype Execution Plan  
**Intelligent Identification of Hazard-Based Red Zones, Carrying Capacity Assessment, and Immediate Relocation Needs for Vulnerable Habitations**

| Field | Value |
|-------|--------|
| **Organization** | Ministry of Home Affairs / NDRF, DM Division |
| **Deadline** | 5 September 2026 |
| **Plan locked** | 27 August 2026 |
| **Working days** | 9 days remaining (27 Aug → 5 Sep) |
| **Team** | 6 people (3–4 active coders) |
| **GIS experience** | None professional — learn minimum only |
| **Priority** | Working end-to-end prototype > perfect architecture |

---

## 0. Executive decision (read first)

### Feasibility scores

| Dimension | Score | Note |
|-----------|------:|------|
| Overall feasibility | **6.5 / 10** | Achievable only with extreme scope cut |
| Data feasibility | **5.5 / 10** | Open data works; official portals are slow/gated |
| GIS difficulty | **7 / 10** | Zero pro GIS is the main risk |
| ML difficulty | **3 / 10** | Do **not** force ML |
| Development difficulty | **6 / 10** | Pipeline glue is harder than any single feature |
| Demo potential | **8.5 / 10** | Explainable map + relocation ranks well |
| Risk of failure | **6 / 10** | Data + GIS learning curve + scope creep |
| **This plan (if followed)** | **78 / 100** | Drops to ~40 if scope expands |

### Proceed?

**Yes — only with amputations.**

**Must sacrifice**
- All of India / full state / multi-district
- All hazards beyond **2**
- Real-time satellite processing
- Neural nets / “fake AI”
- PostGIS, GeoServer, microservices, auth, mobile
- Legal land records, full evacuation logistics
- Perfect Census 2021 microdata

**Keep**
- One Himalayan district
- Landslide + cloudburst/flash-flood
- Explainable multi-criteria scoring
- Real open GIS layers
- Working map → priority → site recommendation → capacity

---

## 1. Locked scope

### Geography: Rudraprayag district, Uttarakhand **only**

| Why | Detail |
|-----|--------|
| Relevance | 2013 Kedarnath / Mandakini — nationally understood multi-hazard story |
| Hazards | Landslide + extreme rainfall / cloudburst flash flood in same valleys |
| Size | ~1,984 km² — rasters stay manageable |
| Data | GSI inventory, DEM, OSM, WorldPop, village boundaries available |
| Demo | Steep terrain + river corridors + clustered habitations = strong visuals |

**Backup (only if village polygons fail by end of Day 2):** Chamoli.  
**Do not switch after Day 2.**  
**Do not add a second district.**

### Hazards: exactly two

1. **Landslide** (slope + historical inventory density + rainfall trigger)
2. **Cloudburst / flash-flood susceptibility** (stream proximity + topographic wetness + extreme rainfall) — *not* plains river hydrology

| Hazard | Data | GIS | Visual | Fit for PS |
|--------|------|-----|--------|------------|
| Landslide | Strong | Medium | Excellent | Perfect |
| Cloudburst / flash flood | Medium | Medium | Excellent | Perfect |
| Plains flood | Medium | Easy | Average | Wrong geography |
| Coastal erosion | Weak | Hard | Weak | Irrelevant |

---

## 2. Datasets (detailed)

### Legend

| Tag | Meaning |
|-----|---------|
| 🟢 | Ready to use / download in hours |
| 🟡 | Usable after clip/join/derive |
| 🟠 | Painful (login, PDF, slow, incomplete) |
| 🔴 | Do not depend on for MVP |

### 2.1 Administrative & settlements

| Dataset | Source | Format | Coverage | Resolution | Free | Process | Tag |
|---------|--------|--------|----------|------------|------|---------|-----|
| District boundary | [DataMeet maps](https://github.com/datameet/maps), [india-geodata](https://yashveeeeeeer.github.io/india-geodata/), geoBoundaries | GeoJSON / SHP | India | vector | Yes | Filter Rudraprayag | 🟢 |
| Village / town polygons | [DataMeet Indian Village Boundaries](https://projects.datameet.org/indian_village_boundaries/) (`ut` / Uttarakhand) | GeoJSON WGS84 | State | vector | Yes | Filter district; join census codes | 🟡 |
| Alt village geometries | [DevDataLab / SHRUG](https://devdatalab.org/shrug) PC11 | GPKG / SHP | India | vector | Yes | Better IDs if DataMeet messy | 🟡 |
| Tehsil / block | Same admin sources | GeoJSON | District | vector | Yes | Optional context layer | 🟢 |

**Join key strategy:** Prefer 2011 census village codes. If join fails → use village name fuzzy match for demo subset + WorldPop for population.

### 2.2 Terrain & hydro

| Dataset | Source | Format | Coverage | Resolution | Free | Process | Tag |
|---------|--------|--------|----------|------------|------|---------|-----|
| DEM | [Copernicus GLO-30](https://spacedata.copernicus.eu/) or [SRTM 30m](https://earthexplorer.usgs.gov/) / OpenTopography | GeoTIFF | Global | 30 m | Yes | Clip to district bbox; reproject | 🟢/🟡 |
| Slope / aspect | Derived (rasterio + numpy / gdaldem) | GeoTIFF | District | 30 m | Yes | From DEM | 🟡 |
| TWI (Topographic Wetness Index) | Derived | GeoTIFF | District | 30 m | Yes | Flow accumulation + slope | 🟡 |
| Rivers / streams | OSM waterways (Geofabrik Asia / Overpass) | GeoJSON / PBF | District | vector | Yes | Filter waterway tags | 🟢 |
| Relative elevation to stream | Derived | GeoTIFF | District | 30 m | Yes | Optional; improve flash-flood | 🟡 |

**CRS rule:** Display EPSG:4326. Compute distances/areas in **EPSG:32644** (UTM zone 44N).

### 2.3 Landslide

| Dataset | Source | Format | Coverage | Notes | Tag |
|---------|--------|--------|----------|-------|-----|
| GSI landslide inventory | [bharatlas GSI inventory](https://bharatlas.com/view/gsi_landslide_inventory) (CC0) | GeoJSON / SHP / Parquet | Pan-India ~30k points | Clip to district; KDE → susceptibility | 🟢 |
| NRSC Landslide Atlas / Bhuvan | [NRSC](https://www.nrsc.gov.in/nrscnew/resources_atlas_landslide.php), Bhuvan | PDF / portal | Himalaya + WG | Context + validation only; login/PDF friction | 🟠 |
| Event literature 2013 | Papers / IMD reports | PDF / text | Kedarnath belt | Demo narrative + sanity check villages | 🟡 |

### 2.4 Rainfall / extreme weather

| Dataset | Source | Format | Coverage | Resolution | Free | Process | Tag |
|---------|--------|--------|----------|------------|------|---------|-----|
| CHIRPS | UCSB CHIRPS | GeoTIFF / NetCDF | Global | ~5 km | Yes | Clip; 99th percentile; June 2013 anomaly | 🟡 |
| ERA5 / ERA5-Land | Copernicus CDS | NetCDF | Global | 0.1° / 0.25° | Yes | Fallback if CHIRPS slow | 🟡 |
| IMD station | IMD portal | CSV | Stations | point | Mixed | Registration; sparse in hills | 🟠 |
| Live IMD / GloFAS ops feed | Operational APIs | API | — | — | Mixed | **Out of MVP** | 🔴 |

### 2.5 Population & vulnerability proxies

| Dataset | Source | Format | Notes | Tag |
|---------|--------|--------|-------|-----|
| Census 2011 village PCA | Census / SHRUG | CSV | Population; age groups if join works | 🟡 |
| WorldPop India | [HDX WorldPop](https://data.humdata.org/dataset/worldpop-population-density-for-india) | GeoTIFF 100 m / 1 km | Scale 2011→recent; fallback if village join fails | 🟢 |
| SECC / deprivation | SHRUG / public extracts | CSV | Optional poverty proxy | 🟡 |
| Census 2021 microdata | ORGI | — | **Not available cleanly in 48h** | 🔴 |

### 2.6 Infrastructure (OSM-first)

| Dataset | Source | Format | Tags to pull | Tag |
|---------|--------|--------|--------------|-----|
| Roads | Geofabrik / Overpass | PBF → GeoJSON | highway=* (primary…track) | 🟢 |
| Hospitals / PHCs | OSM | GeoJSON | amenity=hospital, clinic, doctors | 🟢 |
| Schools | OSM | GeoJSON | amenity=school, college | 🟢 |
| Water points | OSM | GeoJSON | amenity=drinking_water, waterway, natural=water | 🟢 |
| Buildings (optional density) | OSM | GeoJSON | building=* | 🟡 |
| Official HMIS facilities | MoHFW | mixed | Nice-to-have only | 🟠 |
| Official shelters | SDMA PDFs | PDF | Do not block on | 🔴 |

### 2.7 Land cover & relocation candidates

| Dataset | Source | Format | Use | Tag |
|---------|--------|--------|-----|-----|
| ESA WorldCover 10 m | ESA | GeoTIFF | Buildable classes (grass, crop, shrub, bare) | 🟡 |
| ESRI / Dynamic World LULC | Planetary / GEE export | GeoTIFF | Fallback LULC | 🟡 |
| Protected areas | WDPA / OSM park | GeoJSON | Exclude from sites | 🟡 |
| Cadastral / ownership | State revenue | — | **Out of scope** | 🔴 |
| Forest clearance status | FCA | — | **Out of scope** | 🔴 |

### 2.8 Day-1 download checklist (Person 5 + Person 4)

Freeze local folder: `data/rudraprayag/`

1. [ ] Rudraprayag district polygon (GeoJSON)
2. [ ] Uttarakhand villages → filter district
3. [ ] GSI landslide points → clip
4. [ ] DEM tiles covering district (Copernicus or SRTM)
5. [ ] OSM extract (roads, waterways, amenities, landuse)
6. [ ] WorldPop 100 m India → clip
7. [ ] CHIRPS (or ERA5) multi-year + June 2013
8. [ ] ESA WorldCover tile
9. [ ] One-page 2013 disaster fact sheet for demo narrative

**Rule:** After Day 2, no new primary sources unless a file is corrupt. Prefer fixing process over hunting portals.

### 2.9 Fallback matrix

| Need | PRIMARY | FALLBACK | LAST RESORT (label **SYNTHETIC**) |
|------|---------|----------|-----------------------------------|
| District boundary | DataMeet / LGD | geoBoundaries | Hand bbox (debug only) |
| Habitations | DataMeet + Census 2011 | WorldPop clusters as points | 25 named demo villages |
| Landslide | GSI → KDE | Slope > 30° proxy | 15 hand-placed points |
| Flash flood | Dist-to-stream + TWI + rainfall | Dist-to-river only | 200/500/1000 m buffers |
| DEM / slope | Copernicus 30 m | SRTM 30 m | SRTM 90 m |
| Rainfall | CHIRPS | ERA5-Land | Scenario multiplier only |
| Population | Census + WorldPop scale | WorldPop only | Manual pop for demo set |
| Roads / POIs | OSM | — | 5–8 manual POIs |
| LULC / buildable | ESA WorldCover | OSM landuse | Slope < 15° ∩ not water |
| Disaster history | 2013 lists + GSI dates | News geocodes | Single Kedarnath event polygon |

**Never present synthetic as official.** UI must show `Source: …` and `SYNTHETIC` when used.

---

## 3. MVP definition

### End-to-end pipeline

```
Data → Preprocess → Risk → Vulnerability → Red Zones
    → Habitation priority → Site candidates → Capacity
    → Recommendation + Explain → API → Dashboard
```

### Must demonstrate

1. Landslide + flash-flood → multi-hazard → **Red Zones** on map  
2. Habitations with **vulnerability** + **priority** (Immediate / Short / Medium / Monitor)  
3. Click habitation → **recommended relocation site** + **why**  
4. Site shows **capacity / existing / residual**  
5. Officer can use without a developer driving every click  

### Pages (only four)

1. **Overview** — KPIs, district context  
2. **Risk map** — hazards, red zones, habitations, sites  
3. **Habitation panel** — scores, priority, explain  
4. **Relocation planner** — ranked sites + capacity  

### Explicitly out of MVP

Scenario lab, login, PDF reports, routing, 3D terrain, time-series animation, mobile app, live satellite.

---

## 4. Intelligence approach (no forced ML)

| Approach | Verdict |
|----------|---------|
| A. Pure brittle rules | Too weak for judges |
| **B. Weighted multi-criteria (transparent)** | **USE THIS** |
| C. Supervised ML | No labelled relocate/don’t dataset |
| D. Hybrid + ML | Only if B done by 1 Sep (unlikely) |

**Product language:** “AI-assisted GIS decision support” = automated overlay, prioritization, and site ranking — **not** a neural net.

**Judge line:** *We evaluated ML. There is no public labelled relocation set for this district. A black-box model is not auditable for NDRF/SDMA. Explainable MCA matches how DM authorities already reason.*

---

## 5. Algorithms (implementable)

### 5.1 Hazard scores (rasters 0–1, district min-max)

**Inputs**

- \(S\): slope — \(\mathrm{clip}((slope° - 15)/30)\) → 15°→0, 45°→1  
- \(L\): landslide KDE from GSI points (bandwidth ~500 m), min-max  
- \(R\): rainfall severity (CHIRPS 99th pct or June 2013 anomaly), min-max  
- \(W\): wetness / flood path — inverse distance to stream (cap 1 km) + TWI min-max (+ optional low relative elevation)

**Landslide**

\[
H_{ls} = 0.45\,S + 0.40\,L + 0.15\,R
\]

**Flash-flood / cloudburst path**

\[
H_{ff} = 0.50\,W + 0.50\,R
\]

(Simpler first; refine weights only if time.)

**Multi-hazard (probabilistic OR)**

\[
H = 1 - (1 - H_{ls})(1 - H_{ff})
\]

**Red zone classes**

| Class | Condition |
|-------|-----------|
| Red | \(H \ge 0.70\) |
| Orange | \(0.50 \le H < 0.70\) |
| Yellow | \(0.30 \le H < 0.50\) |
| Green | \(H < 0.30\) |

Polygonize red cells; drop polygons &lt; 2 ha.  
**Habitation hazard** = mean \(H\) in polygon (or max in 300 m buffer).

**Degraded mode:** If rainfall missing, drop \(R\) and renormalize weights; UI shows “degraded”.

### 5.2 Vulnerability

| Factor | Proxy | Weight |
|--------|-------|-------:|
| Population size | Census 2011 (± WorldPop scale) | 0.25 |
| Dependents | (0–6)+(60+)/total if available | 0.15 |
| Isolation | Dist to road ≥ tertiary + dist to HQ | 0.20 |
| Health access | Dist to nearest hospital/PHC | 0.15 |
| Historical exposure | GSI count in 1 km + 2013-belt flag | 0.25 |

Normalize 0–1 by district rank/min-max. Missing factor → drop + renormalize.

\[
V = \sum w_i x_i
\]

### 5.3 Relocation priority

\[
P = 0.60\,H_{hab} + 0.40\,V
\]

| \(P\) | Class | Action |
|------:|-------|--------|
| ≥ 0.75 | **Immediate** | Plan relocation / evacuation now |
| 0.60–0.75 | Short-term | This season |
| 0.40–0.60 | Medium-term | Mitigate + monitor |
| &lt; 0.40 | Monitor | Stay, strengthen |

**Override:** If `% area in Red ≥ 40%` OR \(H_{hab} \ge 0.80\) → force **Immediate**.

### 5.4 Candidate sites

1. Fishnet 500 m **or** dissolve buildable LULC classes  
2. Drop mean \(H \ge 0.40\)  
3. Drop mean slope ≥ 20°  
4. Drop if &gt; 30% forest/water/snow/urban  
5. Drop protected areas  
6. Keep residual ≥ 3 ha; merge adjacents  
7. Cap ~8–15 named sites for demo  

**If auto-gen fails:** hand-digitize 10 polygons in geojson.io in 2 hours; method = “expert-screened candidate set”.

### 5.5 Site suitability for habitation \(i\) → site \(j\)

All terms 0–1; higher = better.

| Factor | Definition | Weight |
|--------|------------|-------:|
| Safety | \(1 - H_j\) | 0.30 |
| Distance | \(1 - \mathrm{clip}(d_{ij}/25\,\mathrm{km})\) | 0.15 |
| Road | \(1 - \mathrm{clip}(d_{road}/2\,\mathrm{km})\) | 0.15 |
| Healthcare | \(1 - \mathrm{clip}(d_{hosp}/10\,\mathrm{km})\) | 0.10 |
| School | \(1 - \mathrm{clip}(d_{school}/5\,\mathrm{km})\) | 0.05 |
| Water | \(1 - \mathrm{clip}(d_{water}/1\,\mathrm{km})\) | 0.10 |
| Capacity fit | \(\mathrm{clip}(C^{avail}_j / pop_i,\ 0,\ 1)\) | 0.15 |

\[
U_{ij} = \sum w_k f_k
\]

Recommend \(\arg\max_j U_{ij}\) with \(C^{avail}_j \ge 0.5 \times pop_i\). Else **split** across top 2.

### 5.6 Carrying capacity

\[
A_{safe} = A \times p_{buildable} \times p_{slope&lt;15} \times (1-p_{hazard}) \times (1-p_{protected})
\]

\[
C_{raw} = A_{safe} / 80 \quad (80\ \mathrm{m}^2/\mathrm{person\ planning\ density})
\]

Deraters \(f_{road}, f_{water}, f_{health} \in [0.6, 1.0]\):

\[
C = C_{raw} \times f_{road} \times f_{water} \times f_{health}
\]

\[
C^{avail} = \max(0,\ C - P_{existing})
\]

**Honest UI copy:** First-order physical screening capacity — not statutory land allotment.

### 5.7 Killer feature: Explainable recommendation

Not rainfall-what-if. Not live satellite.

On click, show:

- Why RED / priority (stacked contributions)  
- Why Site B (safety, distance, capacity, access)  
- Runner-up  

Optional **Should-have:** rainfall ×1.2 slider that recomputes \(R\) and \(H\).

---

## 6. Architecture (Cursor-oriented)

### 6.1 Design principles for 10 days

1. **Precompute offline** — demo must not depend on live GIS processing  
2. **GeoJSON + JSON as the contract** — frontend can run static if API dies  
3. **No PostGIS / GeoServer** — SQLite + files  
4. **One monorepo** — Cursor indexes everything; one PR mindset  
5. **Thin API** — serve artifacts + ranking on precomputed JSON  
6. **Parachute** — static React build with `/public/data/*.geojson`

### 6.2 Recommended repo layout (create Day 1 in Cursor)

```text
redzone-dss/
├── README.md                 # runbook, sources, limitations
├── .gitignore
├── .cursor/
│   └── rules/                # optional: project rules for AI assist
│       └── project.md
├── data/                     # NOT committed if large; document how to obtain
│   └── rudraprayag/
│       ├── raw/              # original downloads
│       └── processed/        # clipped tifs, intermediate
├── out/                      # committed small GeoJSON/JSON for demo
│   ├── district.geojson
│   ├── habitations.geojson
│   ├── red_zones.geojson
│   ├── sites.geojson
│   ├── landslides.geojson
│   ├── streams.geojson
│   ├── meta.json             # KPI counts, sources, weights
│   └── recommendations.json
├── config/
│   ├── weights.yaml          # all MCA weights + thresholds
│   └── paths.yaml
├── scripts/                  # run in order; each is CLI-friendly
│   ├── 01_preprocess.py      # clip, reproject, slope, TWI
│   ├── 02_risk_engine.py     # H_ls, H_ff, H, red polygons
│   ├── 03_vuln_engine.py     # V, P, priority
│   ├── 04_relocation.py      # sites, C, U_ij
│   ├── 05_export.py          # write out/* + meta
│   └── requirements.txt
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI
│   │   ├── routers/
│   │   │   ├── district.py
│   │   │   ├── habitations.py
│   │   │   ├── layers.py
│   │   │   └── recommend.py
│   │   ├── schemas.py        # Pydantic = JSON contract
│   │   └── data_loader.py    # read out/* once at startup
│   ├── requirements.txt
│   └── tests/
│       └── test_api_smoke.py
├── frontend/
│   ├── package.json
│   ├── index.html
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/client.ts     # fetch helpers; fallback to /data
│   │   ├── types.ts          # mirrors Pydantic
│   │   ├── pages/
│   │   │   ├── Overview.tsx
│   │   │   ├── RiskMap.tsx
│   │   │   ├── HabitationPanel.tsx
│   │   │   └── RelocationPlanner.tsx
│   │   ├── components/
│   │   │   ├── MapView.tsx
│   │   │   ├── LayerToggles.tsx
│   │   │   ├── ExplainPanel.tsx
│   │   │   └── KpiCards.tsx
│   │   └── styles/
│   └── public/
│       └── data/             # copy of out/* for static parachute
└── docs/
    ├── sources.md
    ├── methodology.md        # formulas + weight justification
    ├── demo_script.md
    └── judge_faq.md
```

### 6.3 JSON contract (freeze end of Day 1)

```json
{
  "id": "UT_RUD_0123",
  "name": "Example Village",
  "block": "Ukhimath",
  "pop": 850,
  "lat": 30.52,
  "lon": 79.10,
  "h_ls": 0.78,
  "h_ff": 0.61,
  "h": 0.82,
  "v": 0.71,
  "p": 0.78,
  "priority": "Immediate",
  "pct_red": 46.0,
  "rec_site_id": "SITE_B",
  "rec_score": 0.81,
  "explain": [
    {"factor": "multi_hazard", "value": 0.82, "weight": 0.60, "contribution": 0.49},
    {"factor": "vulnerability", "value": 0.71, "weight": 0.40, "contribution": 0.28}
  ],
  "why_site": [
    "H_site=0.18 (below 0.40 safety filter)",
    "Spare capacity 1120 ≥ 0.5×850",
    "Road 220 m; PHC 4.1 km"
  ]
}
```

Frontend and backend share this shape. Mock it on Day 1 so UI is not blocked.

### 6.4 Tech stack (one)

| Layer | Choice | Why |
|-------|--------|-----|
| Frontend | React (Vite) + TypeScript | Team already knows; fast |
| Map | Leaflet + react-leaflet | Simplest; good enough |
| Backend | Python 3.11 + FastAPI | Fast to write; auto OpenAPI |
| GIS | geopandas, rasterio, shapely, pyproj, numpy | Minimum pro stack |
| DB | SQLite optional; prefer files | No PostGIS learning tax |
| ML | **None** | — |
| Auth | **None** | — |
| Deploy | Single VM / Render / Railway / laptop offline | Demo reliability |

### 6.5 Runtime architecture

```text
data/rudraprayag/raw
        │
        ▼
scripts/01→05  (laptop batch, Cursor terminal)
        │
        ▼
out/*.geojson + meta.json + recommendations.json
        │
        ├──────────────────────┐
        ▼                      ▼
   FastAPI (uvicorn)     frontend/public/data (static parachute)
        │
        ▼
 React + Leaflet dashboard
        │
        ▼
 SDMA / NDRF officer (demo)
```

### 6.6 API surface (minimal)

| Method | Path | Returns |
|--------|------|---------|
| GET | `/api/health` | ok |
| GET | `/api/district` | bounds, KPIs, sources |
| GET | `/api/habitations` | FeatureCollection or list |
| GET | `/api/habitations/{id}` | full explain payload |
| GET | `/api/layers/{name}` | GeoJSON file stream |
| GET | `/api/sites` | candidate sites + capacity |
| GET | `/api/recommend/{hab_id}` | top site + runner-up + reasons |

### 6.7 Database (optional SQLite)

Only if file joins get messy. Tables:

- `habitations` — scores + geometry ref  
- `sites` — capacity fields  
- `recommendations` — hab_id, site_id, rank, u_score, reasons_json  
- `events` — 2013 Kedarnath etc.  

**No users table.**

### 6.8 Working in Cursor — team practice

| Practice | Detail |
|----------|--------|
| **One repo** | Everyone clones; branch per person or pair |
| **Cursor rules** | Put stack + “no PostGIS / no ML” in `.cursor/rules` so AI assist does not invent microservices |
| **Terminal** | Run `scripts/0x_*.py` from Cursor integrated terminal; keep `data/` local |
| **Split terminals** | P1: uvicorn `--reload`; P3: `npm run dev` |
| **Contract first** | Pydantic models + `types.ts` written before features |
| **Mock data** | `out/habitations.geojson` with 5 fake features Day 1 |
| **Commits** | Small; never commit multi-GB GeoTIFFs — use `data/README.md` with download links |
| **Pair GIS** | P2 + P4 same window Days 1–3 (CRS bugs need two pairs of eyes) |
| **Definition of done** | Feature works against `out/` artifacts, not “notebook looks good” |
| **Static parachute** | Script copies `out/` → `frontend/public/data/`; client falls back if API fails |

### 6.9 Local runbook (README must include)

```bash
# GIS pipeline (once data is in place)
cd scripts && python 01_preprocess.py && python 02_risk_engine.py && \
  python 03_vuln_engine.py && python 04_relocation.py && python 05_export.py

# API
cd backend && uvicorn app.main:app --reload --port 8000

# UI
cd frontend && npm install && npm run dev
```

Demo laptop: pre-run scripts; only start API + UI.

---

## 7. Team roles

| ID | Role | Codes? |
|----|------|--------|
| **P1** | Backend + architecture + glue + static parachute | Yes |
| **P2** | Risk / vuln / relocation Python engines | Yes |
| **P3** | React + Leaflet dashboard | Yes |
| **P4** | GIS preprocess (pair with P2) | Yes / learning |
| **P5** | Data hunt, citations, domain, weights memo, judge FAQ | No |
| **P6** | UI copy, testing, PPT, demo script, video backup | Light |

Do not reshuffle after Day 1.

---

## 8. Day-by-day plan

### Day 0–1 — 27 Aug: Freeze + data in the box

**Objective:** Scope locked, repo exists, downloads started, dummy map.

| Person | Work |
|--------|------|
| P1 | Repo layout, FastAPI `/health`, JSON schema, folder structure |
| P2 | Formula unit tests on dummy numpy arrays; `weights.yaml` |
| P3 | Vite + React + Leaflet + dummy GeoJSON points |
| P4 | Install geopandas/rasterio; clip district; first slope map |
| P5 | Full Day-1 download list; sources spreadsheet |
| P6 | 4-screen wireframe; legend colors (red/orange/yellow/green) |

**DoD:** Everyone runs something; dummy map in browser; DEM clipped.  
**Kill if:** Still arguing district/hazards.

### 28 Aug — First real hazard

P1: `/api/habitations` from GeoJSON  
P2+P4: \(H_{ls}\) on real raster; start stream distance for \(H_{ff}\)  
P3: Choropleth + click popup  
P5: Sanity-check 5 villages vs 2013 reports  
P6: Popup copy  

**Cut if rasters broken by 22:00:** Vector-only mode (buffers + slope samples). Stop rasterio debugging.

### 29 Aug — Multi-hazard + Red

P2: \(H\), thresholds, polygonize  
P4: UTM areas  
P1: `/api/layers/redzone`  
P3: Red overlay + priority colors  
P5: Threshold memo  

**Cut if polygonize ugly:** PNG raster overlay instead of polygons.

### 30 Aug — **MVP-0 gate (most important night)**

**Must have**

- Working map  
- 1–2 hazard layers  
- Red overlay  
- Habitation scores via API  
- React talking to FastAPI  

If missing → **cancel fancy relocation**; spend 31 Aug–2 Sep making this bulletproof.

### 31 Aug — Vulnerability + priority

P2: \(V\), \(P\), force-Immediate  
P1: explain payload  
P3: Habitation drawer + stacked bars  
P4: Distances to road/hospital  
P5+P2: Feel-check 10 villages  
P6: FAQ draft  

### 1 Sep — Sites + capacity

P2+P4: 8–15 sites, \(C\)  
P1: `/api/sites`, `/api/recommend/{id}`  
P3: Site markers + planner table  
P5: Real place names (verify not in river)  
**Cut if auto-gen fails:** 10 hand-drawn sites  

### 2 Sep — Ranking + explain (killer)

P2: \(U_{ij}\), top-1 + runner-up, reason strings  
P1: Stable explain API  
P3: “Why RED / Why site” panel  
P6: Demo rehearsal #1 (record)  
**Cut if ranking buggy:** Sort by \(1-H\) then distance  

### 3 Sep — Harden only

No new formulas. CORS, gzip, simplify vertices, README runbook, static parachute.  
P5: Sources + limitations slides  
P6: PPT + demo script lock  

### 4 Sep — Demo minus one

Full run-through ×3. Video backup. Feature freeze 18:00.  
Offline laptop path verified.

### 5 Sep — Freeze

Crash fixes only. P6 presents; P1 drives map; P2 methods; P5 data.

---

## 9. Daily cut rules

| When | If missing | Cut to |
|------|------------|--------|
| 26 Aug night | District not chosen | Captain locks Rudraprayag |
| 27 Aug | Village polygons fail | WorldPop points as habitations |
| 28 Aug | Raster pipeline broken | Vector buffers only |
| 29 Aug | Second hazard weak | Stream buffer + optional rainfall slider later |
| **30 Aug** | Map+API+score broken | Drop relocation intelligence |
| 31 Aug | Census join fail | Pop + distances only |
| 1 Sep | Site gen fail | Hand-digitized sites |
| 2 Sep | Ranking fail | Deterministic safety + distance sort |
| Any day | “Add Chamoli / PyTorch / PostGIS” | **No** |

---

## 10. What not to build

- Deep learning on satellite imagery  
- All-India / multi-district  
- Live Sentinel / GEE in demo loop  
- PostGIS, GeoServer, Kubernetes, Redis, Kafka  
- Microservices, GraphQL  
- Auth / SSO  
- Mobile app  
- Cesium 3D  
- OSRM routing  
- OR-Tools optimization  
- LLM “chat with the map”  
- Blockchain land records  
- Trying for NDRF MoU in 10 days  

---

## 11. Failure plan

| Failure | Response |
|---------|----------|
| GIS data fails | Day-2 frozen GeoJSON; vector buffers |
| API fails on Wi-Fi | Static React + `/public/data` |
| “ML poor” | There is no ML |
| PostGIS hard | Never start it |
| Frontend behind | One HTML + Leaflet CDN + GeoJSON |
| Coder unavailable | P1↔P3 merge; P2 exports GeoJSON from scripts alone |
| Laptop dies | Nightly zip of `data/` + `out/` on two drives + cloud |
| Layer in the ocean | Forgot CRS — `to_crs(4326)` checklist |

---

## 12. Demo script (5 minutes)

1. **0:00–0:25** Hook — 2013 memory; relocation is reactive; this is pre-monsoon screening.  
2. **0:25–0:50** Overview KPIs — habitations, Immediate count, % area Red.  
3. **0:50–1:40** Risk map — GSI points, flash-flood path, multi-hazard, red polygons. Explain OR formula in one sentence.  
4. **1:40–2:40** Click village — Immediate + stacked “why”.  
5. **2:40–3:50** Recommend Site B — capacity, distance, H, runner-up.  
6. **3:50–4:20** Limitations — screening ≠ legal notification; capacity ≠ revenue approval.  
7. **4:20–5:00** Deploy path — field verify, forest/revenue overlay, human-in-loop.

---

## 13. Judge FAQ (short form)

Full answers live in `docs/judge_faq.md`. Core positions:

- **Data is real open data; scores are our model** — not official NDMA zonation.  
- **Weights are documented expert defaults**, not fitted AUC cosplay.  
- **No ML** because no labelled relocation target and auditability matters.  
- **Red** = multi-hazard \(H \ge 0.70\) screening threshold (policy knob).  
- **Capacity** = physical first-order, not statutory.  
- **Sites safer on our layers**, not geotechnically certified.  
- **One district is discipline**, not weakness.  
- **Dynamic** = rerun pipeline when layers update — not 5-minute satellite.  
- **Not “just QGIS”** — prioritization + capacity + explain in one officer workflow.

---

## 14. Future scope (post-prototype / Phase 2–3)

Ship the MVP first. These are **roadmap slides**, not Day-1 tickets.

### Phase 2 — Pilot hardening (1–2 months)

| Item | Description |
|------|-------------|
| Official boundary swap | Replace DataMeet with Survey of India / LGD certified layers |
| GSI / NRSC refresh | Periodic landslide inventory update job |
| IMD / state rainfall | District rainfall grids or station interpolation |
| Forest + revenue overlays | Exclude non-leasable land from capacity |
| Weight workshop | SDMA + GSI + CWC set weights; sensitivity UI |
| Field verification app | Mobile form: “confirm / reject red polygon” → feedback store |
| Bilingual UI | Hindi + English |
| PDF one-pager | Auto summary per habitation for file noting |
| Multi-district batch | Same pipeline, tiled rasters, queue of districts |

### Phase 3 — State DSS (6–12 months)

| Item | Description |
|------|-------------|
| Uttarakhand-wide | All high-risk districts; shared site pool |
| Additional hazards | GLOF, erosion where data exists — modular hazard plugins |
| Live triggers | IMD heavy-rainfall warnings rescale \(R\) overnight |
| Building exposure | C-band / optical building footprints for exposure |
| Population nowcasting | WorldPop / HRSL annual updates |
| Role-based access | SDMA planner vs district officer vs public summary |
| Audit trail | Every recommendation versioned with data hash + weights |
| Integration | IDRN, NDMA portals, state emergency ops center |

### Phase 4 — National pattern (12–24 months)

| Item | Description |
|------|-------------|
| Hazard plugin SDK | States add coastal erosion, cyclone surge, etc. |
| Standard MCA profiles | NDMA-endorsed weight profiles per hazard family |
| Secure NIC hosting | Air-gapped option for sensitive layers |
| ML **where labels exist** | e.g. landslide susceptibility if inventory is rich — still explainable hybrid |
| Community consultation layer | Consent / objection status per habitation |

**Architecture implication (design now, build later):**

- Keep `weights.yaml` and hazard modules **pluggable**  
- Do not hardcode “Rudraprayag” deep in engines — pass `district_id` + paths  
- Export `meta.json` with data hashes so Phase 3 audit is possible  
- Avoid PostGIS until multi-user editing is a real requirement  

---

## 15. Must / Should / Cut

### Must have

- Map with 2 hazards + red zones  
- Habitation priority  
- ≥1 recommended site per high-priority habitation  
- Capacity numbers  
- Explain panel  
- Sources + limitations  
- Static backup demo  

### Should have (only after Must)

- Rainfall scenario slider  
- Split relocation across 2 sites  
- 2013 event overlay  
- PDF one-pager  
- Hindi labels  

### Cut without guilt

- ML, PostGIS, second district, third hazard, Cesium, routing, auth, chat LLM, mobile  

---

## 16. Final product concept

**RedZone DSS** is a district-scale, explainable GIS decision-support prototype for Rudraprayag that maps landslide and cloudburst/flash-flood hazard, paints screening Red Zones, scores habitation vulnerability and relocation priority, and ranks safer sites with first-order carrying capacity — so an SDMA officer can go from a map to a named, justified recommendation in one click.

---

## 17. Tonight’s 6 actions (no meeting &gt; 45 min)

1. Lock Rudraprayag + landslide + flash flood in README  
2. Create monorepo with layout in §6.2  
3. Start Day-1 downloads into `data/rudraprayag/raw`  
4. P3: Leaflet + 5 dummy points  
5. P2: formulas in tested Python with fake arrays  
6. P6: 4-screen wireframe  

---

## 18. Document control

| Version | Date | Note |
|---------|------|------|
| 1.0 | 26 Aug 2026 | Initial ruthless plan |
| 2.0 | 27 Aug 2026 | Rebased to 9-day execution window; added Cursor master implementation prompt, demo-mode contract, provenance, and integration gates |

**Owner:** Team lead / P1  
**Rule:** Scope changes require captain + written cut of something else of equal size.

---

*Working Prototype > Perfect Architecture · Realistic Data > Imaginary Data · Simple GIS > Advanced GIS · Explainable Scoring > Fake AI · Complete Flow > Fifty Half-Built Features · Demo Reliability > Technical Complexity*


---

# 19. ULTIMATE CURSOR IMPLEMENTATION PROMPT

> **Purpose:** Paste this entire section into Cursor Agent/Plan mode at the root of the repository. Cursor must treat this as the authoritative implementation contract. It must inspect the repository before proposing code, preserve the locked MVP, and optimize for a working demo by **5 September 2026**.

## MASTER PROMPT — PS 26191 RedZone DSS

You are the lead software architect and implementation planner for **SIH 2026 Problem Statement 26191 — Intelligent Identification of Hazard-Based Red Zones, Carrying Capacity Assessment, and Immediate Relocation Needs for Vulnerable Habitations**.

We have **9 calendar days remaining (27 Aug → 5 Sep 2026)**. We are building a **working, judge-ready prototype**, not a production disaster-management system.

### 1. Your first job: inspect before planning

Before changing any file:

1. Inspect the entire repository tree.
2. Read existing `README`, package manifests, Python requirements, configuration files, frontend entry points, backend entry points, existing scripts, and tests.
3. Identify what already works and what is missing.
4. Do NOT recreate an existing working module.
5. Do NOT introduce a new framework because it is fashionable.
6. Do NOT assume data exists. Inspect the actual `data/` and `out/` directories.
7. Produce a short **Current State Audit** containing:
   - existing stack
   - runnable commands
   - working features
   - broken features
   - missing features
   - risky dependencies
   - files that should not be touched
8. Then produce the implementation plan.

### 2. Locked product scope — DO NOT EXPAND

The prototype is restricted to:

- **Geography:** Rudraprayag district, Uttarakhand.
- **Hazards:** 
  1. Landslide
  2. Cloudburst / flash-flood susceptibility
- **Core workflow:**

```text
Real/open data
    ↓
Preprocessing
    ↓
Hazard scoring
    ↓
Multi-hazard Red Zones
    ↓
Habitation vulnerability
    ↓
Relocation priority
    ↓
Candidate safer sites
    ↓
Carrying capacity
    ↓
Site ranking
    ↓
Explainable recommendation
    ↓
Officer dashboard
```

The dashboard must let a user move from:

**Map → habitation → priority → why → recommended relocation site → capacity → runner-up**

### 3. Absolutely forbidden scope creep

Do NOT add any of these to the MVP:

- All-India mapping
- second district
- third hazard
- deep learning
- computer vision
- satellite image inference in the demo loop
- PostGIS
- GeoServer
- Kubernetes
- Redis
- Kafka
- microservices
- GraphQL
- authentication
- mobile application
- Cesium/3D
- OSRM/routing
- OR-Tools optimization
- LLM chatbot
- blockchain
- full evacuation logistics
- legal land ownership/cadastral logic
- statutory zoning claims
- real-time operational integrations

If a feature is suggested, classify it as **Phase 2 / Phase 3**, never silently add it to MVP.

### 4. Product positioning

The system is:

**“An AI-assisted, explainable GIS decision-support prototype.”**

Do not falsely claim that it uses a trained neural network.

The intelligence comes from:

- automated GIS overlays
- multi-criteria hazard scoring
- vulnerability scoring
- relocation prioritization
- candidate-site screening
- capacity estimation
- explainable ranking

Use this positioning consistently in UI copy, README, PPT-facing documentation, and API descriptions.

### 5. Technical stack

Prefer:

- Frontend: React + Vite + TypeScript
- Map: Leaflet + react-leaflet
- Backend: Python 3.11 + FastAPI
- GIS: GeoPandas, Rasterio, Shapely, PyProj, NumPy
- Data contract: GeoJSON + JSON
- Storage: files first; SQLite only if genuinely necessary
- ML: none
- Deployment: local/offline-first, with optional simple deployment

If the repository already uses a compatible stack, preserve it.

Do not migrate frameworks merely for cleanup.

### 6. Architecture principle: precompute, don't compute during demo

All expensive GIS operations must happen offline through scripts.

Runtime should primarily:

1. load precomputed artifacts;
2. expose lightweight API endpoints;
3. render the map;
4. display scores/recommendations.

The frontend must have a **static parachute**:

```text
API available
    → fetch API

API unavailable
    → load /data/*.geojson and JSON directly
```

The demo must still work if Wi-Fi disappears after the application has loaded.

### 7. Required repository structure

Use this structure unless the current repository has an equivalent structure that is already working:

```text
redzone-dss/
├── README.md
├── .gitignore
├── .cursor/
│   └── rules/
│       └── project.md
├── data/
│   └── rudraprayag/
│       ├── raw/
│       ├── processed/
│       └── README.md
├── out/
│   ├── district.geojson
│   ├── habitations.geojson
│   ├── red_zones.geojson
│   ├── sites.geojson
│   ├── landslides.geojson
│   ├── streams.geojson
│   ├── meta.json
│   └── recommendations.json
├── config/
│   ├── weights.yaml
│   └── paths.yaml
├── scripts/
│   ├── 01_preprocess.py
│   ├── 02_risk_engine.py
│   ├── 03_vuln_engine.py
│   ├── 04_relocation.py
│   └── 05_export.py
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   ├── schemas.py
│   │   └── data_loader.py
│   └── tests/
└── frontend/
    ├── src/
    └── public/
        └── data/
```

### 8. Mathematical contract — do not silently change

Implement the following as configuration-driven logic.

#### Landslide

```text
H_ls = 0.45*S + 0.40*L + 0.15*R
```

Where:

- `S` = normalized slope severity
- `L` = normalized landslide-density/KDE signal
- `R` = normalized rainfall severity

#### Flash-flood / cloudburst path

```text
H_ff = 0.50*W + 0.50*R
```

Where:

- `W` = stream proximity + wetness/topographic signal
- `R` = rainfall severity

#### Multi-hazard

```text
H = 1 - (1-H_ls)*(1-H_ff)
```

#### Red-zone classes

```text
H >= 0.70       Red
0.50–<0.70     Orange
0.30–<0.50     Yellow
<0.30           Green
```

#### Vulnerability

```text
V = weighted sum of:
population size        0.25
dependents             0.15
isolation              0.20
health access          0.15
historical exposure    0.25
```

Missing factors must be removed and remaining weights renormalized.

#### Relocation priority

```text
P = 0.60*H_hab + 0.40*V
```

```text
P >= 0.75       Immediate
0.60–<0.75      Short-term
0.40–<0.60      Medium-term
<0.40           Monitor
```

Force Immediate when:

```text
pct_red >= 40%
OR
H_hab >= 0.80
```

Do not modify these thresholds without documenting the change.

### 9. Site screening contract

Candidate sites must be screened by:

- hazard
- slope
- land-cover/buildability
- protected-area exclusion
- minimum residual area

Preferred filters:

```text
mean hazard < 0.40
mean slope < 20°
protected area = false
residual area >= 3 ha
```

### 10. Carrying capacity contract

Use the first-order physical screening model:

```text
A_safe =
A
× p_buildable
× p_slope<15
× (1-p_hazard)
× (1-p_protected)
```

Then:

```text
C_raw = A_safe / 80
```

Apply access deraters:

```text
C = C_raw * f_road * f_water * f_health
```

And:

```text
C_available = max(0, C - existing_population)
```

UI must call this:

**“First-order physical screening capacity”**

Never call it statutory carrying capacity, approved settlement capacity, or legally available land.

### 11. Recommendation contract

For habitation `i` and site `j`:

```text
U_ij =
0.30*safety
+ 0.15*distance
+ 0.15*road
+ 0.10*healthcare
+ 0.05*school
+ 0.10*water
+ 0.15*capacity_fit
```

Recommend the highest-scoring site with:

```text
C_available >= 0.5 * habitation_population
```

If no single site qualifies, allow a split recommendation across the top two sites.

Every recommendation must include:

- score
- site ID
- site name
- safety
- distance
- road access
- healthcare access
- water access
- capacity
- runner-up
- reason strings

### 12. Data provenance is a first-class feature

Every major output must retain source metadata.

`meta.json` should contain at minimum:

```json
{
  "district": "Rudraprayag",
  "generated_at": "...",
  "model_version": "...",
  "sources": [],
  "weights_version": "...",
  "degraded_mode": false,
  "synthetic_data_used": false,
  "limitations": []
}
```

For every layer, distinguish:

- `OFFICIAL`
- `OPEN_DATA`
- `DERIVED`
- `EXPERT_SCREENED`
- `SYNTHETIC`

Never label derived scores as official government hazard zones.

If synthetic data is used, make it visibly obvious in the UI and metadata.

### 13. API contract

Implement only what is necessary:

```text
GET /api/health
GET /api/district
GET /api/habitations
GET /api/habitations/{id}
GET /api/layers/{name}
GET /api/sites
GET /api/recommend/{hab_id}
```

Return stable JSON shapes.

Use Pydantic models where practical.

Do not make the frontend depend on internal Python implementation details.

### 14. Frontend requirements

Only four major views:

1. Overview
2. Risk Map
3. Habitation Panel
4. Relocation Planner

Risk Map must support:

- district boundary
- hazard layers
- red zones
- habitation points/polygons
- candidate sites
- legend
- layer toggles

Habitation interaction must show:

- name
- population
- hazard score
- vulnerability score
- priority class
- percentage in Red Zone
- explanation

Recommendation panel must show:

- recommended site
- capacity
- available capacity
- suitability score
- reasons
- runner-up

Avoid excessive animations and UI decoration.

The product should look like a serious **government decision-support dashboard**, not a consumer app.

### 15. Demo data fallback is mandatory

If official/open datasets cannot be fully processed in time:

- use the best available real data;
- reduce the number of habitations;
- use expert-screened candidate sites;
- use deterministic derived values;
- clearly mark synthetic/expert-screened components.

Never spend the final 48 hours fighting one broken portal.

### 16. Required implementation order

Do NOT implement pages randomly.

Use these gates:

#### Gate 1 — Foundation

Must work:

- repository
- frontend starts
- backend starts
- `/api/health`
- dummy GeoJSON loads
- map renders

#### Gate 2 — Hazard

Must work:

- district
- landslide layer
- flash-flood proxy
- multi-hazard score
- red-zone layer

#### Gate 3 — Habitation intelligence

Must work:

- habitation data
- hazard score
- vulnerability
- priority
- explanation

#### Gate 4 — Relocation

Must work:

- candidate sites
- capacity
- site ranking
- recommendation
- runner-up

#### Gate 5 — Demo hardening

Must work:

- API fallback
- source labels
- error states
- loading states
- README
- clean startup
- no broken buttons
- stable demo path

### 17. Nine-day execution plan

#### 27 Aug — Day 1

Foundation + data acquisition.

Deliver:

- repo structure
- Cursor rules
- frontend shell
- backend shell
- dummy contract
- first real datasets
- map rendering

#### 28 Aug — Day 2

First real hazard.

Deliver:

- DEM/slope
- landslide layer
- stream proximity
- rainfall input if available
- first hazard score

#### 29 Aug — Day 3

Multi-hazard Red Zone.

Deliver:

- H_ls
- H_ff
- H
- red/orange/yellow/green
- polygonized red zones
- UTM area calculations

#### 30 Aug — Day 4 — MVP-0 GATE

Required:

- working map
- 1–2 hazards
- red zones
- habitations
- API integration

If this gate fails:

**STOP relocation work.**

Harden the map and hazard pipeline.

#### 31 Aug — Day 5

Vulnerability + priority.

Deliver:

- vulnerability score
- priority class
- force-Immediate override
- habitation drawer
- explanation panel

#### 1 Sep — Day 6

Sites + capacity.

Deliver:

- 8–15 candidate sites
- capacity
- existing/residual capacity
- site markers
- planner

#### 2 Sep — Day 7

Recommendation intelligence.

Deliver:

- U_ij
- top recommendation
- runner-up
- reasons
- stable recommendation API

#### 3 Sep — Day 8

Hardening.

Deliver:

- fallback mode
- source/provenance labels
- performance cleanup
- error handling
- README
- reproducible startup
- no new formulas

#### 4 Sep — Day 9

Demo freeze.

Deliver:

- three complete rehearsals
- offline test
- backup copy
- screenshot/video backup
- feature freeze

#### 5 Sep

Only crash fixes.

### 18. Definition of Done

Do not say a feature is complete because code exists.

A feature is DONE only when:

1. it runs;
2. it uses the agreed data contract;
3. it renders correctly or returns the expected API;
4. it handles missing data;
5. it has at least one meaningful test or validation;
6. it does not break the previous gate;
7. it can be demonstrated in under 30 seconds.

### 19. Testing requirements

At minimum create tests for:

- hazard score range is `[0,1]`
- multi-hazard score is `[0,1]`
- priority thresholds
- Immediate override
- missing-factor weight renormalization
- capacity never becomes negative
- recommendation only selects eligible sites
- recommendation has a runner-up when possible
- API health
- habitation endpoint
- recommendation endpoint

Also add one small deterministic fixture so the scoring engine can be tested without downloading GIS data.

### 20. CRS safety

Use:

```text
EPSG:4326
```

for display.

Use:

```text
EPSG:32644
```

for distances and areas.

Every GIS script must make CRS assumptions explicit.

Add validation so a layer accidentally interpreted in degrees cannot silently produce absurd distances/areas.

### 21. Performance rules

Do not:

- send large rasters to the browser;
- perform KDE in the API request;
- calculate every site's score on every click if it can be precomputed;
- load multi-GB files into frontend memory;
- polygonize on request.

Precompute and simplify GeoJSON.

### 22. Cursor working rules

Create `.cursor/rules/project.md` containing the non-negotiable constraints:

```text
Project: PS 26191 RedZone DSS

Deadline: 5 Sep 2026

Locked geography: Rudraprayag
Locked hazards: Landslide + cloudburst/flash flood

No:
- ML
- PostGIS
- GeoServer
- microservices
- auth
- mobile
- 3D
- second district
- third hazard

Prefer:
- Python 3.11
- FastAPI
- React + TypeScript
- Leaflet
- GeoJSON
- precomputed GIS
- offline-first demo

Never label derived scores as official hazard zonation.
Never label screening capacity as statutory capacity.
Never use synthetic data without explicit metadata/UI labeling.
```

### 23. How you must work with us

When asked to implement a feature:

1. Explain which gate the feature belongs to.
2. List files you will create/change.
3. Explain dependencies.
4. Implement the smallest working version.
5. Run tests/build/type checks where available.
6. Report exactly what passed and failed.
7. Do not silently modify formulas.
8. Do not silently add dependencies.
9. Do not refactor unrelated code.
10. If a dependency or dataset is unavailable, provide the fallback path immediately.

### 24. What your FIRST response must contain

Do not immediately dump code.

Your first response after inspecting the repository must contain exactly these sections:

```text
# 1. Current State Audit
# 2. Architecture Decision
# 3. Gap Analysis
# 4. Critical Risks
# 5. Day-by-Day Implementation Plan
# 6. File-by-File Change Plan
# 7. Data Requirements
# 8. MVP Acceptance Tests
# 9. Demo Path
# 10. First Implementation Batch
```

For **First Implementation Batch**, specify the exact files to create/change and the exact order in which they should be implemented.

Then wait for implementation approval unless the user has explicitly asked Cursor to begin coding.

### 25. Final success criterion

The prototype succeeds if a judge can perform this flow without developer assistance:

```text
Open dashboard
    ↓
See Rudraprayag
    ↓
See hazard/red zones
    ↓
Click vulnerable habitation
    ↓
See Immediate/Short/Medium/Monitor
    ↓
See why
    ↓
Click recommendation
    ↓
See safer site
    ↓
See capacity + residual capacity
    ↓
See why this site was selected
    ↓
See runner-up
```

The winning strategy is:

**realistic data + transparent scoring + GIS visualization + actionable relocation recommendation + honest limitations + reliable demo.**

Do not optimize for technical novelty at the expense of completing this flow.

---

# 20. Cursor execution checklist

Use this as the team's control board while Cursor implements the plan.

- [ ] Cursor has inspected the existing repository before changing architecture.
- [ ] `.cursor/rules/project.md` exists.
- [ ] Frontend starts.
- [ ] Backend starts.
- [ ] `/api/health` works.
- [ ] Dummy GeoJSON renders.
- [ ] Rudraprayag boundary is loaded.
- [ ] Landslide layer is loaded.
- [ ] Flash-flood/cloudburst proxy is loaded.
- [ ] Multi-hazard score is generated.
- [ ] Red zones render.
- [ ] Habitations render.
- [ ] Vulnerability score works.
- [ ] Priority class works.
- [ ] Explain panel works.
- [ ] Candidate sites render.
- [ ] Capacity works.
- [ ] Recommendation works.
- [ ] Runner-up works.
- [ ] Source labels work.
- [ ] Synthetic/degraded mode is clearly labeled.
- [ ] Static fallback works.
- [ ] API smoke tests pass.
- [ ] Frontend production build passes.
- [ ] Full demo works from a clean start.
- [ ] No new feature is added after feature freeze.

---

# 21. Final team rule

If a proposed feature cannot make the judge's core journey better, safer, more explainable, or more reliable by 5 September, **do not build it**.

**Working Prototype > Perfect Architecture**

**Realistic Data > Imaginary Data**

**Explainable Intelligence > Fake AI**

**Complete Workflow > Fifty Features**

**Demo Reliability > Technical Complexity**
