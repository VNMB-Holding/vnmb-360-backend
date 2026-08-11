from pydantic import BaseModel, ConfigDict
from typing import Optional
from decimal import Decimal

class RealEstateBase(BaseModel):
    upload_id: Optional[int] = None
    description: str
    market_value: Optional[Decimal] = None

class RealEstateCreate(RealEstateBase):
    pass

class RealEstateResponse(RealEstateBase):
    id: int
    upload_id: int
    model_config = ConfigDict(from_attributes=True)
