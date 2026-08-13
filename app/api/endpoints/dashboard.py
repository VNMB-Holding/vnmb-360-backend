from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.db.session import get_db
from app.services.dashboard import DashboardService
from app.schemas.summary import DashboardSummaryResponse, EvolutionPoint

router = APIRouter()

@router.get("/dashboard/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    upload_id: Optional[int] = Query(None, description="Filter summary by spreadsheet upload_id (defaults to latest upload)"),
    db: Session = Depends(get_db)
):
    return DashboardService.get_summary(db, upload_id=upload_id)

@router.get("/dashboard/history", response_model=List[EvolutionPoint])
def get_dashboard_history(
    upload_id: Optional[int] = Query(None, description="Filter history by spreadsheet upload_id (defaults to latest upload)"),
    db: Session = Depends(get_db)
):
    return DashboardService.get_history(db, upload_id)


