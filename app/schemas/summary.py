from pydantic import BaseModel
from typing import Optional
from datetime import date
from decimal import Decimal

class DashboardSummaryResponse(BaseModel):
    upload_id: Optional[int] = None
    upload_filename: Optional[str] = None
    total_real_estate: Decimal
    total_vehicles: Decimal
    total_livestock: Decimal
    total_investments: Decimal
    latest_investment_date: Optional[date] = None
    total_debts: Decimal
    latest_debt_date: Optional[date] = None
    net_worth: Decimal
