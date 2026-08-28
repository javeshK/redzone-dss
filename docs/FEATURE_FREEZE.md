# Feature Freeze — RedZone DSS

**Effective:** 28 August 2026 (Day 9 demo freeze)  
**Presentation:** 5 September 2026

## Frozen scope

The MVP is **feature-complete**. No new formulas, hazards, districts, or major UI flows after this date.

### In scope (locked)

| Area | Delivered |
|------|-----------|
| Hazard pipeline | H_ls, H_ff, H, red/orange/yellow zones |
| Vulnerability | 5-factor V, priority P, Immediate override |
| Relocation | 11 screened sites, U_ij ranking, runner-up, reasons |
| API | Read-only FastAPI + static fallback |
| UI | Overview, Risk Map, Habitation Panel, Relocation Planner |
| Hardening | Provenance badges, degraded/synthetic banners, error retry |

### Allowed after freeze (5 Sep only)

- Crash fixes that restore an already-demonstrated flow
- Copy/typo fixes that do not change scoring or data contracts
- Demo machine setup (paths, ports, env)

### Not allowed

- New scoring factors or weight changes
- Third hazard type or second district
- Auth, ML, PostGIS, microservices
- New dashboard pages or API endpoints unless required to fix a crash

## Demo data contract

Frozen artifacts in `out/` and `frontend/public/data/`:

- 25 habitations (`UT_RUD_0001`–`UT_RUD_0025`)
- 11 screened relocation sites
- 25 recommendations (top + runner-up + comparison)
- `meta.json` with KPIs, sources, limitations

## Verification before presenting

```bash
python scripts/run_demo_rehearsal.py
```

Or step-by-step:

```bash
python scripts/validate_demo.py
python scripts/offline_demo_test.py
cd backend && pytest tests/ -q
cd frontend && npm run build
```

## Team roles (5 Sep)

| Person | Role |
|--------|------|
| P6 | Present / narrate |
| P1 | Drive map + habitation clicks |
| P2 | Explain scoring methods |
| P5 | Data sources + limitations |
