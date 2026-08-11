from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from app.db.base import Base

class LivestockInventory(Base):
    __tablename__ = "livestock_inventory"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("excel_upload_log.id", ondelete="CASCADE"), nullable=False, index=True)
    unit = Column(String(100), nullable=True)
    owner = Column(String(100), nullable=True)
    location_type = Column(String(100), nullable=True)
    contract_id = Column(String(50), nullable=True)
    cattle_partner = Column(String(255), nullable=True)
    head_count = Column(Integer, nullable=True)
    total_value = Column(Numeric(15, 2), nullable=True)
    avg_per_head = Column(Numeric(10, 2), nullable=True)
    total_farm_weight = Column(Numeric(10, 2), nullable=True)
    total_freight_per_head = Column(Numeric(10, 2), nullable=True)
    total_commission = Column(Numeric(15, 2), nullable=True)
