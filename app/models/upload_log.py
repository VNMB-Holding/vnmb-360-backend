from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime, timezone
from app.db.base import Base

def utc_now():
    return datetime.now(timezone.utc)

class ExcelUploadLog(Base):
    __tablename__ = "excel_upload_log"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime, default=utc_now, nullable=False, index=True)
    records_ingested = Column(JSON, nullable=True)
    summary_metrics = Column(JSON, nullable=True)

