# Demo Rehearsal Checklist

Use this for **three complete run-throughs** before 5 September.  
Target: **under 5 minutes** per run (see `demo_script.md`).

Record at least one run for **video backup**. Save **screenshots** of each main view.

---

## Pre-flight (once per machine)

- [ ] `python scripts/run_demo_rehearsal.py` — all automated steps PASS
- [ ] `out/rehearsal_report.json` exists and `"passed": true`
- [ ] Backup zip in `backups/` (from `backup_demo.py`)
- [ ] Browser zoom 100%, full screen, bookmarks cleared of distractions
- [ ] Close unrelated apps; disable notifications

---

## Run-through script (repeat ×3)

### A. Cold start (2 min)

- [ ] Terminal 1: `cd backend && uvicorn app.main:app --port 8000`
- [ ] Terminal 2: `cd frontend && npm run dev`
- [ ] Open http://localhost:5173
- [ ] Confirm banner shows **API mode** (or static if API intentionally off)

### B. Overview (30 sec)

- [ ] KPI cards: habitations, Immediate count, red-zone area
- [ ] Mention synthetic/degraded banner if visible
- [ ] Point to data sources + limitations sections

### C. Risk Map (90 sec)

- [ ] Toggle: district, red zones, landslides, streams, habitations, sites
- [ ] Click **Ukhimath** — popup / selection works
- [ ] State: derived scores, not official zonation

### D. Habitation Panel (60 sec)

- [ ] Navigate to Habitation → Ukhimath
- [ ] Show H, V, P, % red, priority **Immediate**
- [ ] Open explanation table (hazard + vulnerability factors)
- [ ] Mention override reason if shown

### E. Relocation Planner (90 sec)

- [ ] Open recommendation for Ukhimath
- [ ] Show top site, U_ij score, capacity + **available** capacity
- [ ] Read 2–3 reason strings
- [ ] Show runner-up + comparison panel (Δ U_ij, distance)

### F. Offline resilience (30 sec) — at least once across 3 runs

- [ ] Stop API (`Ctrl+C` on uvicorn)
- [ ] Refresh browser — static fallback banner appears
- [ ] Confirm Overview + Map + Planner still load

### G. Fully offline path — at least once

- [ ] `cd frontend && npm run build && npm run preview`
- [ ] Open http://localhost:4173 (no API)
- [ ] Complete steps B–E on preview build

---

## Screenshot backup (minimum set)

Save to `docs/demo_snapshots/screenshots/` (create folder if needed):

1. `01_overview.png` — KPI cards + limitations
2. `02_risk_map.png` — layers on, habitation selected
3. `03_habitation_explain.png` — Ukhimath scores + explain table
4. `04_planner_recommendation.png` — top + runner-up cards
5. `05_offline_banner.png` — static fallback banner visible

---

## Rehearsal log

| Run | Date | Duration | Offline OK? | Issues | Fixed? |
|-----|------|----------|-------------|--------|--------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

---

## If something breaks during rehearsal

| Issue | Quick fix |
|-------|-----------|
| Empty map | `python scripts/05_export.py` |
| 404 on API | Check `out/` exists; restart uvicorn from `backend/` |
| Wrong scores | Re-run pipeline `01`–`05` (allow ~5 min) |
| Build fails | `cd frontend && npm install && npm run build` |
| Tests fail | `cd backend && pytest tests/ -v` for details |

**Do not** add features during rehearsal — log issues and fix only if they block the demo.
