from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date

from app.db.session import get_db
from app.models import FinancialInvestment, ExcelUploadLog
from app.schemas.investment import FinancialInvestmentResponse

router = APIRouter()

@router.get("/investments", response_model=List[FinancialInvestmentResponse])
def get_investments(
    upload_id: Optional[int] = Query(None, description="Filter investments by spreadsheet upload_id (defaults to latest upload if not provided)"),
    reference_date: Optional[date] = Query(None, description="Filter investments by reference date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    if upload_id is None:
        upload_id = db.query(func.max(ExcelUploadLog.id)).scalar()
        if upload_id is None:
            return []

    query = db.query(FinancialInvestment).filter(FinancialInvestment.upload_id == upload_id)
        
    if reference_date:
        query = query.filter(FinancialInvestment.reference_date == reference_date)

    return query.order_by(FinancialInvestment.reference_date.desc(), FinancialInvestment.asset_name.asc()).all()
