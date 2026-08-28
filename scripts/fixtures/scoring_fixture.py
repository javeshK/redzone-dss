"""Deterministic fixture for scoring engine tests — no GIS data required."""

FIXTURE_GRID = {
    "slope": [0.0, 0.5, 1.0],
    "landslide_density": [0.0, 0.5, 1.0],
    "rainfall": [0.5, 0.5, 0.5],
    "wetness": [0.0, 0.5, 1.0],
}

FIXTURE_HABITATION = {
    "id": "TEST_001",
    "h_ls": 0.78,
    "h_ff": 0.61,
    "factors": {"population": 0.8, "isolation": 0.6},
    "pct_red": 46.0,
}

FIXTURE_SITE = {
    "id": "SITE_TEST",
    "p_hazard": 0.22,
    "area_ha": 10.0,
    "p_buildable": 0.7,
    "p_slope_lt15": 0.85,
    "p_protected": 0.0,
    "existing_pop": 100,
    "f_road": 0.9,
    "f_water": 0.85,
    "f_health": 0.8,
}
