# Demo Script — RedZone DSS (5 minutes)

## Setup (before judges arrive)

1. Pre-run GIS pipeline: `cd scripts && python 01_preprocess.py && ... && python 05_export.py`
2. Start API: `cd backend && uvicorn app.main:app --port 8000`
3. Start UI: `cd frontend && npm run dev`
4. Open http://localhost:5173 in browser

## Narration Script

### 1. Overview (30 sec)

"This is RedZone DSS — an explainable GIS decision-support prototype for Rudraprayag district. It identifies hazard-based red zones, scores habitation vulnerability, and recommends safer relocation sites with first-order physical screening capacity."

Point to KPI cards: habitations, Immediate priority count, red-zone area.

Note the synthetic/expert-screened banner if visible.

### 2. Risk Map (90 sec)

Navigate to **Risk Map**.

- Toggle layers: district boundary, red/orange/yellow zones, landslide inventory, streams
- "Red zones are derived from multi-criteria hazard scoring — landslide and flash-flood — not official government zonation."
- Click **Ukhimath** — high-priority habitation in red zone corridor

### 3. Habitation Intelligence (60 sec)

Navigate to **Habitation** (or click through from map).

- Show priority class: **Immediate**
- Show H, V, P scores and % in Red Zone
- Open explanation table: multi-hazard and vulnerability contributions
- "Immediate is forced because 46% of habitation area falls in red zone."

### 4. Relocation Recommendation (90 sec)

Click **View Relocation Recommendation** or go to **Relocation Planner**.

- Top site: Okhimath Plateau North, suitability score
- Capacity: show total and **available** capacity
- Emphasize: "First-order physical screening capacity — not statutory capacity"
- Read 2–3 reason strings
- Show **runner-up** site for comparison

### 5. Offline Resilience (30 sec, optional)

Stop the API server. Refresh the page.

"The dashboard still works from precomputed static data — critical for field demos without reliable connectivity."

## Closing

"We combine realistic open data, transparent scoring, and actionable relocation recommendations — with honest limitations clearly labeled."

---

## Rehearsal notes (Day 9 freeze)

- Run **three full rehearsals** using `docs/REHEARSAL_CHECKLIST.md`
- Automated pre-check: `python scripts/run_demo_rehearsal.py`
- Record **one run** as video backup; save **5 screenshots** (see checklist)
- Feature freeze is active — see `docs/FEATURE_FREEZE.md`
- On demo day (5 Sep): crash fixes only; P6 presents, P1 drives the map

### Timing targets

| Section | Target |
|---------|--------|
| Overview | 30 s |
| Risk Map | 90 s |
| Habitation | 60 s |
| Relocation | 90 s |
| Offline (optional) | 30 s |
| **Total** | **~5 min** |

### Fallback narration (if API dies mid-demo)

"The system is designed for field use — it falls back to precomputed artifacts bundled with the dashboard. All scores and recommendations remain available offline."
