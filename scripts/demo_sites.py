"""Expert-screened candidate relocation sites for Rudraprayag demo (12 sites)."""

DEMO_SITES = [
    {
        "id": "SITE_A", "name": "Okhimath Plateau North", "lon": 79.05, "lat": 30.55,
        "area_ha": 24.0, "p_buildable": 0.72, "p_slope_lt15": 0.85, "p_hazard": 0.22, "p_protected": 0.0,
        "existing_pop": 200, "f_road": 0.90, "f_water": 0.85, "f_health": 0.80, "f_school": 0.70,
    },
    {
        "id": "SITE_B", "name": "Guptkashi Ridge East", "lon": 79.10, "lat": 30.54,
        "area_ha": 16.0, "p_buildable": 0.68, "p_slope_lt15": 0.80, "p_hazard": 0.28, "p_protected": 0.0,
        "existing_pop": 180, "f_road": 0.85, "f_water": 0.80, "f_health": 0.75, "f_school": 0.65,
    },
    {
        "id": "SITE_C", "name": "Phata Valley Bench", "lon": 79.02, "lat": 30.42,
        "area_ha": 10.5, "p_buildable": 0.75, "p_slope_lt15": 0.88, "p_hazard": 0.31, "p_protected": 0.05,
        "existing_pop": 120, "f_road": 0.78, "f_water": 0.90, "f_health": 0.65, "f_school": 0.60,
    },
    {
        "id": "SITE_D", "name": "Augustmuni Terrace", "lon": 78.89, "lat": 30.36,
        "area_ha": 14.0, "p_buildable": 0.70, "p_slope_lt15": 0.82, "p_hazard": 0.25, "p_protected": 0.0,
        "existing_pop": 150, "f_road": 0.82, "f_water": 0.88, "f_health": 0.72, "f_school": 0.68,
    },
    {
        "id": "SITE_E", "name": "Srinagar Riverside Flat", "lon": 78.80, "lat": 30.24,
        "area_ha": 18.5, "p_buildable": 0.65, "p_slope_lt15": 0.78, "p_hazard": 0.30, "p_protected": 0.02,
        "existing_pop": 220, "f_road": 0.88, "f_water": 0.92, "f_health": 0.78, "f_school": 0.72,
    },
    {
        "id": "SITE_F", "name": "Chopta Meadow South", "lon": 79.20, "lat": 30.68,
        "area_ha": 12.0, "p_buildable": 0.68, "p_slope_lt15": 0.75, "p_hazard": 0.27, "p_protected": 0.08,
        "existing_pop": 80, "f_road": 0.72, "f_water": 0.80, "f_health": 0.60, "f_school": 0.55,
    },
    {
        "id": "SITE_G", "name": "Pipalkoti Foothill", "lon": 79.33, "lat": 30.38,
        "area_ha": 15.5, "p_buildable": 0.74, "p_slope_lt15": 0.83, "p_hazard": 0.29, "p_protected": 0.0,
        "existing_pop": 190, "f_road": 0.86, "f_water": 0.82, "f_health": 0.70, "f_school": 0.66,
    },
    {
        "id": "SITE_H", "name": "Kalimath Bench West", "lon": 78.99, "lat": 30.47,
        "area_ha": 11.0, "p_buildable": 0.71, "p_slope_lt15": 0.84, "p_hazard": 0.26, "p_protected": 0.0,
        "existing_pop": 110, "f_road": 0.80, "f_water": 0.86, "f_health": 0.68, "f_school": 0.62,
    },
    {
        "id": "SITE_I", "name": "Joshiyara Plateau", "lon": 78.96, "lat": 30.27,
        "area_ha": 13.5, "p_buildable": 0.73, "p_slope_lt15": 0.86, "p_hazard": 0.24, "p_protected": 0.0,
        "existing_pop": 140, "f_road": 0.84, "f_water": 0.87, "f_health": 0.74, "f_school": 0.70,
    },
    {
        "id": "SITE_J", "name": "Narayankoti Slope Base", "lon": 79.04, "lat": 30.48,
        "area_ha": 9.5, "p_buildable": 0.69, "p_slope_lt15": 0.79, "p_hazard": 0.33, "p_protected": 0.0,
        "existing_pop": 95, "f_road": 0.79, "f_water": 0.84, "f_health": 0.66, "f_school": 0.60,
    },
    {
        "id": "SITE_K", "name": "Deoria Riverside", "lon": 79.11, "lat": 30.44,
        "area_ha": 8.5, "p_buildable": 0.67, "p_slope_lt15": 0.77, "p_hazard": 0.32, "p_protected": 0.03,
        "existing_pop": 85, "f_road": 0.77, "f_water": 0.88, "f_health": 0.64, "f_school": 0.58,
    },
    {
        "id": "SITE_L", "name": "Makku Valley Floor", "lon": 79.17, "lat": 30.64,
        "area_ha": 11.5, "p_buildable": 0.70, "p_slope_lt15": 0.81, "p_hazard": 0.28, "p_protected": 0.05,
        "existing_pop": 70, "f_road": 0.74, "f_water": 0.83, "f_health": 0.62, "f_school": 0.56,
    },
]

# Candidates that fail screening (retained for audit, excluded from output)
REJECTED_SITES = [
    {
        "id": "SITE_X1", "name": "Steep Slope Reject", "lon": 79.25, "lat": 30.60,
        "area_ha": 6.0, "p_buildable": 0.40, "p_slope_lt15": 0.35, "p_hazard": 0.55, "p_protected": 0.0,
        "existing_pop": 0, "f_road": 0.50, "f_water": 0.50, "f_health": 0.50, "f_school": 0.50,
        "reject_reason": "Mean slope exceeds 20° threshold",
    },
    {
        "id": "SITE_X2", "name": "High Hazard Reject", "lon": 79.08, "lat": 30.51,
        "area_ha": 4.0, "p_buildable": 0.60, "p_slope_lt15": 0.70, "p_hazard": 0.72, "p_protected": 0.0,
        "existing_pop": 0, "f_road": 0.60, "f_water": 0.60, "f_health": 0.60, "f_school": 0.60,
        "reject_reason": "Mean hazard >= 0.40",
    },
]
