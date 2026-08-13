from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app.db.session import get_db
from app.models import VehicleFleet, ExcelUploadLog
from app.schemas.vehicle import VehicleFleetResponse

router = APIRouter()

@router.get("/vehicles", response_model=List[VehicleFleetResponse])
def get_vehicles(
    upload_id: Optional[int] = Query(None, description="Filter vehicles by spreadsheet upload_id (defaults to latest upload if not provided)"),
    db: Session = Depends(get_db)
):
    if upload_id is None:
        upload_id = db.query(func.max(ExcelUploadLog.id)).scalar()
        if upload_id is None:
            return []

    query = db.query(VehicleFleet).filter(VehicleFleet.upload_id == upload_id)

    return query.order_by(VehicleFleet.id.asc()).all()
