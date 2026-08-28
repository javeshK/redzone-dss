from fastapi import APIRouter, HTTPException

from app.data_loader import store
from app.schemas import HabitationDetail, HabitationSummary

router = APIRouter()


@router.get("", response_model=list[HabitationSummary])
def list_habitations() -> list[HabitationSummary]:
    return store.list_habitations()


@router.get("/{hab_id}", response_model=HabitationDetail)
def get_habitation(hab_id: str) -> HabitationDetail:
    hab = store.get_habitation(hab_id)
    if not hab:
        raise HTTPException(status_code=404, detail=f"Habitation {hab_id} not found")
    return hab
