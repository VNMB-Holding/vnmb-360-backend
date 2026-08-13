from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from app.db.session import get_db
from app.models import LivestockInventory, ExcelUploadLog
from app.schemas.livestock import LivestockInventoryResponse

router = APIRouter()

@router.get("/livestock", response_model=List[LivestockInventoryResponse])
def get_livestock(
    upload_id: Optional[int] = Query(None, description="Filter livestock by spreadsheet upload_id (defaults to latest upload if not provided)"),
    db: Session = Depends(get_db)
):
    if upload_id is None:
        upload_id = db.query(func.max(ExcelUploadLog.id)).scalar()
        if upload_id is None:
            return []

    query = db.query(LivestockInventory).filter(LivestockInventory.upload_id == upload_id)

    return query.order_by(LivestockInventory.id.asc()).all()
