from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from app.db.base import Base

class VehicleFleet(Base):
    __tablename__ = "vehicle_fleet"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("excel_upload_log.id", ondelete="CASCADE"), nullable=False, index=True)
    vehicle_description = Column(String(255), nullable=False)
    manufacture_year = Column(Integer, nullable=True)
    model_year = Column(Integer, nullable=True)
    age = Column(Integer, nullable=True)
    chassis = Column(String(50), nullable=True)
    license_plate = Column(String(20), nullable=True)
    risk_region = Column(String(100), nullable=True)
    assigned_to = Column(String(100), nullable=True)
    market_value = Column(Numeric(15, 2), nullable=True)
    annual_premium = Column(Numeric(10, 2), nullable=True)
    iof_tax = Column(Numeric(10, 2), nullable=True)
    insurance_value = Column(Numeric(15, 2), nullable=True)
    insurance_type = Column(String(50), nullable=True)
