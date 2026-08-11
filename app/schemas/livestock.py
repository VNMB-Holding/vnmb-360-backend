from pydantic import BaseModel, ConfigDict
from typing import Optional
from decimal import Decimal

class LivestockInventoryBase(BaseModel):
    upload_id: Optional[int] = None
    unit: Optional[str] = None
    owner: Optional[str] = None
    location_type: Optional[str] = None
    contract_id: Optional[str] = None
    cattle_partner: Optional[str] = None
    head_count: Optional[int] = None
    total_value: Optional[Decimal] = None
    avg_per_head: Optional[Decimal] = None
    total_farm_weight: Optional[Decimal] = None
    total_freight_per_head: Optional[Decimal] = None
    total_commission: Optional[Decimal] = None

class LivestockInventoryCreate(LivestockInventoryBase):
    pass

class LivestockInventoryResponse(LivestockInventoryBase):
    id: int
    upload_id: int
    model_config = ConfigDict(from_attributes=True)
