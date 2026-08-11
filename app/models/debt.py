from sqlalchemy import Column, Integer, Numeric, Date, ForeignKey
from app.db.base import Base

class DebtControl(Base):
    __tablename__ = "debt_control"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("excel_upload_log.id", ondelete="CASCADE"), nullable=False, index=True)
    reference_date = Column(Date, nullable=False, index=True)
    initial_balance = Column(Numeric(15, 2), nullable=True)
    funding_amount = Column(Numeric(15, 2), nullable=True)
    repayments = Column(Numeric(15, 2), nullable=True)
    interest = Column(Numeric(15, 2), nullable=True)
    final_balance = Column(Numeric(15, 2), nullable=True)
    avg_cdi_percentage = Column(Numeric(5, 4), nullable=True)
