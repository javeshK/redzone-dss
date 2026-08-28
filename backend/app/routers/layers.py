from fastapi import APIRouter, HTTPException

from app.data_loader import store

router = APIRouter()

ALLOWED_LAYERS = {
    "district",
    "habitations",
    "red_zones",
    "sites",
    "landslides",
    "streams",
}


@router.get("/{name}")
def get_layer(name: str) -> dict:
    if name not in ALLOWED_LAYERS:
        raise HTTPException(status_code=404, detail=f"Layer '{name}' not found")
    layer = store.get_layer(name)
    if layer is None:
        raise HTTPException(status_code=404, detail=f"Layer '{name}' not found")
    return layer
