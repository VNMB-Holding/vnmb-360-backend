from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional
from decimal import Decimal

class DebtControlBase(BaseModel):
    upload_id: Optional[int] = None
    reference_date: date
    initial_balance: Optional[Decimal] = None
    funding_amount: Optional[Decimal] = None
    repayments: Optional[Decimal] = None
    interest: Optional[Decimal] = None
    final_balance: Optional[Decimal] = None
    avg_cdi_percentage: Optional[Decimal] = None

class DebtControlCreate(DebtControlBase):
    pass

class DebtControlResponse(DebtControlBase):
    id: int
    upload_id: int
    model_config = ConfigDict(from_attributes=True)
