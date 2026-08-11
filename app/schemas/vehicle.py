from pydantic import BaseModel, ConfigDict
from typing import Optional
from decimal import Decimal

class VehicleFleetBase(BaseModel):
    upload_id: Optional[int] = None
    vehicle_description: str
    manufacture_year: Optional[int] = None
    model_year: Optional[int] = None
    age: Optional[int] = None
    chassis: Optional[str] = None
    license_plate: Optional[str] = None
    risk_region: Optional[str] = None
    assigned_to: Optional[str] = None
    market_value: Optional[Decimal] = None
    annual_premium: Optional[Decimal] = None
    iof_tax: Optional[Decimal] = None
    insurance_value: Optional[Decimal] = None
    insurance_type: Optional[str] = None

class VehicleFleetCreate(VehicleFleetBase):
    pass

class VehicleFleetResponse(VehicleFleetBase):
    id: int
    upload_id: int
    model_config = ConfigDict(from_attributes=True)
