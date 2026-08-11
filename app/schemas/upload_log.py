from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any

class ExcelUploadLogResponse(BaseModel):
    id: int
    filename: str
    uploaded_at: datetime
    records_ingested: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
