from fastapi import APIRouter

from app.data_loader import store
from app.schemas import DistrictResponse, HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    store.load()
    meta = store.get_meta()
    return HealthResponse(
        status="ok",
        district=meta.district,
        model_version=meta.model_version,
        data_loaded=store.is_loaded,
    )


@router.get("/district", response_model=DistrictResponse)
def district() -> DistrictResponse:
    store.load()
    meta = store.get_meta()
    fc = store.get_district_geojson()
    props = {}
    if fc.get("features"):
        props = fc["features"][0].get("properties", {})
    return DistrictResponse(
        name=props.get("name", meta.district),
        state=props.get("state", "Uttarakhand"),
        district_code=props.get("district_code", "UT_RUD"),
        bbox=store.get_district_bbox(),
        geojson=fc,
        meta=meta,
    )
