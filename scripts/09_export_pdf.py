#!/usr/bin/env python3
"""09_export_pdf.py — One-page PDF summary per habitation (reportlab)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import REPO_ROOT, load_paths

IST = timezone(timedelta(hours=5, minutes=30))

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


def _draw_habitation_pdf(c: canvas.Canvas, hab: dict, rec: dict | None, meta: dict) -> None:
    props = hab["properties"]
    width, height = A4
    y = height - 2 * cm

    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, y, f"RedZone DSS — {props['name']}")
    y -= 0.8 * cm

    c.setFont("Helvetica", 9)
    c.drawString(2 * cm, y, f"Habitation ID: {props['id']}  |  Block: {props.get('block', '—')}")
    y -= 0.5 * cm
    c.drawString(2 * cm, y, f"Population: {props.get('pop', '—')}  |  Generated: {meta.get('generated_at', '—')[:19]}")
    y -= 1 * cm

    c.setFont("Helvetica-Bold", 11)
    c.drawString(2 * cm, y, "Hazard & Vulnerability Scores")
    y -= 0.7 * cm
    c.setFont("Helvetica", 10)
    for label, key in [("Multi-hazard (H)", "h"), ("Landslide (H_ls)", "h_ls"),
                       ("Flash-flood (H_ff)", "h_ff"), ("Vulnerability (V)", "v"),
                       ("Priority (P)", "p")]:
        c.drawString(2.5 * cm, y, f"{label}: {props.get(key, 0):.3f}")
        y -= 0.45 * cm

    c.drawString(2.5 * cm, y, f"Priority class: {props.get('priority', '—')}")
    y -= 0.45 * cm
    c.drawString(2.5 * cm, y, f"Red zone coverage: {props.get('pct_red', 0):.1f}%")
    y -= 1 * cm

    if rec and rec.get("top"):
        top = rec["top"]
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2 * cm, y, "Top Relocation Site")
        y -= 0.7 * cm
        c.setFont("Helvetica", 10)
        c.drawString(2.5 * cm, y, f"Site: {top.get('site_name', '—')} (score {top.get('score', 0):.3f})")
        y -= 0.45 * cm
        c.drawString(2.5 * cm, y, f"Distance: {top.get('distance_km', 0):.1f} km  |  Capacity: {top.get('capacity_available', 0)}")
        y -= 0.7 * cm
        c.setFont("Helvetica-Bold", 10)
        c.drawString(2.5 * cm, y, "Reasons:")
        y -= 0.5 * cm
        c.setFont("Helvetica", 9)
        for reason in top.get("reasons", [])[:4]:
            c.drawString(3 * cm, y, f"• {reason[:80]}")
            y -= 0.4 * cm

    y = 3 * cm
    c.setFont("Helvetica-Oblique", 7)
    c.drawString(2 * cm, y, "LIMITATIONS: Derived scores are not official government hazard zonation.")
    c.drawString(2 * cm, y - 0.35 * cm, "Capacity is first-order physical screening capacity, not statutory capacity.")


def main() -> None:
    paths = load_paths()
    pdf_dir = REPO_ROOT / paths["out_dir"] / "pdf"
    pdf_dir.mkdir(parents=True, exist_ok=True)

    if not HAS_REPORTLAB:
        placeholder = {
            "generated_at": datetime.now(IST).isoformat(),
            "status": "reportlab_not_installed",
            "note": "Install reportlab to generate PDFs: pip install reportlab",
            "pdf_dir": str(pdf_dir),
        }
        (REPO_ROOT / paths["out_dir"] / "pdf_manifest.json").write_text(
            json.dumps(placeholder, indent=2), encoding="utf-8"
        )
        print("  [warn] reportlab not installed — wrote pdf_manifest.json placeholder")
        return

    hab_path = REPO_ROOT / paths["out"]["habitations"]
    rec_path = REPO_ROOT / paths["out"]["recommendations"]
    meta_path = REPO_ROOT / paths["out"]["meta"]
    habs = json.loads(hab_path.read_text(encoding="utf-8")) if hab_path.exists() else {"features": []}
    recs = json.loads(rec_path.read_text(encoding="utf-8")).get("recommendations", {}) if rec_path.exists() else {}
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}

    generated = []
    for feat in habs.get("features", []):
        hab_id = feat["properties"]["id"]
        pdf_path = pdf_dir / f"{hab_id}.pdf"
        c = canvas.Canvas(str(pdf_path), pagesize=A4)
        _draw_habitation_pdf(c, feat, recs.get(hab_id), meta)
        c.save()
        generated.append({"habitation_id": hab_id, "file": pdf_path.name})

    manifest = {
        "generated_at": datetime.now(IST).isoformat(),
        "count": len(generated),
        "files": generated,
    }
    (REPO_ROOT / paths["out_dir"] / "pdf_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(f"  Generated {len(generated)} PDFs in {pdf_dir}")
    print("09_export_pdf.py complete.")


if __name__ == "__main__":
    main()
