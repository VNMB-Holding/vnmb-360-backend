from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional
from decimal import Decimal

class FinancialInvestmentBase(BaseModel):
    upload_id: Optional[int] = None
    asset_name: str
    reference_date: date
    amount: Optional[Decimal] = None
    portfolio_weight: Optional[Decimal] = None

class FinancialInvestmentCreate(FinancialInvestmentBase):
    pass

class FinancialInvestmentResponse(FinancialInvestmentBase):
    id: int
    upload_id: int
    model_config = ConfigDict(from_attributes=True)
