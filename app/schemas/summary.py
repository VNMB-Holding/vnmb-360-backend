from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from decimal import Decimal

class EvolutionPoint(BaseModel):
    semana: str
    valor: float
    display_val: str

class DashboardSummaryResponse(BaseModel):
    upload_id: Optional[int] = None
    upload_filename: Optional[str] = None
    total_real_estate: Decimal
    total_vehicles: Decimal
    total_livestock: Decimal
    total_investments: Decimal
    latest_investment_date: Optional[date] = None
    total_caixa: Decimal = Decimal("0.00")
    total_debts: Decimal
    latest_debt_date: Optional[date] = None
    net_worth: Decimal
    
    # Financial metrics for executive dashboard
    weekly_variation_val: Decimal
    weekly_variation_pct: float
    accumulated_variation_val: Decimal
    accumulated_variation_pct: float
    cdi_weekly_pp: float
    cdi_weekly_pct_cdi: float
    cdi_accumulated_pp: float
    cdi_accumulated_pct_cdi: float
    
    # Timeline evolution
    evolution_history: List[EvolutionPoint] = []
