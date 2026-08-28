from fastapi import APIRouter, HTTPException

from app.data_loader import store
from app.schemas import RecommendationResponse, SiteSummary

router = APIRouter()


@router.get("/sites", response_model=list[SiteSummary])
def list_sites() -> list[SiteSummary]:
    return store.list_sites()


@router.get("/recommend/{hab_id}", response_model=RecommendationResponse)
def get_recommendation(hab_id: str) -> RecommendationResponse:
    rec = store.get_recommendation(hab_id)
    if not rec:
        raise HTTPException(
            status_code=404, detail=f"Recommendation for {hab_id} not found"
        )
    return rec
