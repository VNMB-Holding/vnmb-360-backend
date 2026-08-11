from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Literal, Optional

from app.db.session import get_db
from app.models import DebtControl, ExcelUploadLog
from app.schemas.debt import DebtControlResponse

router = APIRouter()

@router.get("/debts", response_model=List[DebtControlResponse])
def get_debts(
    upload_id: Optional[int] = Query(None, description="Filter debts by specific spreadsheet upload_id (defaults to latest upload)"),
    sort_order: Literal["asc", "desc"] = Query("asc", description="Sort order by reference_date"),
    db: Session = Depends(get_db)
):
    if upload_id is None:
        upload_id = db.query(func.max(ExcelUploadLog.id)).scalar()

    query = db.query(DebtControl)
    if upload_id is not None:
        query = query.filter(DebtControl.upload_id == upload_id)

    if sort_order == "desc":
        query = query.order_by(DebtControl.reference_date.desc())
    else:
        query = query.order_by(DebtControl.reference_date.asc())
        
    return query.all()
