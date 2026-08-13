from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app.db.session import get_db
from app.models import RealEstate, ExcelUploadLog
from app.schemas.real_estate import RealEstateResponse

router = APIRouter()

@router.get("/real-estate", response_model=List[RealEstateResponse])
def get_real_estate(
    upload_id: Optional[int] = Query(None, description="Filter real estate by spreadsheet upload_id (defaults to latest upload if not provided)"),
    db: Session = Depends(get_db)
):
    if upload_id is None:
        upload_id = db.query(func.max(ExcelUploadLog.id)).scalar()
        if upload_id is None:
            return []

    query = db.query(RealEstate).filter(RealEstate.upload_id == upload_id)

    return query.order_by(RealEstate.id.asc()).all()
