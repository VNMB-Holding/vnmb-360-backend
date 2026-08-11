from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from app.db.base import Base

class RealEstate(Base):
    __tablename__ = "real_estate"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("excel_upload_log.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(String(255), nullable=False)
    market_value = Column(Numeric(15, 2), nullable=True)
