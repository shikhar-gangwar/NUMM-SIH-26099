from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List, Any

class ImportBatchDTO(BaseModel):
    id: str
    cpse_id: str
    kind: str
    filename: str
    sha256: str
    total_rows: int
    accepted_rows: int
    rejected_rows: int
    warning_rows: int
    status: str
    uploaded_by: str
    created_at: datetime

class ImportResultDTO(BaseModel):
    batch: ImportBatchDTO
    row_reports: List[dict] = []
