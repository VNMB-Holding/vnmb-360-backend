from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey
from app.db.base import Base

class FinancialInvestment(Base):
    __tablename__ = "financial_investment"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("excel_upload_log.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_name = Column(String(255), nullable=False)
    reference_date = Column(Date, nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=True)
    portfolio_weight = Column(Numeric(5, 4), nullable=True)
