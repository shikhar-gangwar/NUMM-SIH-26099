from pydantic import BaseModel
from typing import Optional, Dict, Any

class AuditEventDTO(BaseModel):
    seq: int
    ts: str
    actor_id: Optional[str] = None
    actor_role: str
    action: str
    entity_type: str
    entity_id: str
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None
    model_refs: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    prev_hash: str
    hash: str

class AuditVerifyResultDTO(BaseModel):
    valid: bool
    total_events: int
    broken_seq: Optional[int] = None
    verified_at: str
