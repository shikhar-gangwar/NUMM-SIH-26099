from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.api.schemas.material import MaterialDTO

class MatchRunCreateDTO(BaseModel):
    scope: Optional[Dict[str, Any]] = None # e.g. {"batch_id": "..."}, {"cpse_code": "..."}, {"all": True}
    mode: Optional[str] = "LIVE" # LIVE, SHADOW, SIH_DEMO
    force: Optional[bool] = False

class MatchRunResponseDTO(BaseModel):
    id: str
    scope: Optional[Dict[str, Any]] = None
    mode: str = "LIVE"
    config_versions: Optional[Dict[str, Any]] = None
    stats: Optional[Dict[str, Any]] = None
    status: str
    started_by: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

class MatchRunActiveStatusDTO(BaseModel):
    is_active: bool
    current_run: Optional[MatchRunResponseDTO] = None
    last_completed_run: Optional[MatchRunResponseDTO] = None


class AttributeEditDTO(BaseModel):
    material_id: str
    key: str
    value: Any
    unit: Optional[str] = None

class ReviewDecisionRequest(BaseModel):
    client_decision_id: str
    decision: str # APPROVE, REJECT, MODIFY, ESCALATE, REVOKE
    human_relationship: Optional[str] = None
    target_nmc: Optional[str] = None
    attribute_edits: Optional[List[AttributeEditDTO]] = None
    reason_code: Optional[str] = None
    comment: Optional[str] = None

class MatchEvidenceDTO(BaseModel):
    id: str
    match_id: str
    kind: str
    payload: Optional[Dict[str, Any]] = None
    score: Optional[float] = None
    verdict: Optional[str] = None

class PairResultDTO(BaseModel):
    id: str
    run_id: str
    material_a: MaterialDTO
    material_b: MaterialDTO
    relationship: str
    equivalence_confidence: float
    raw_score: float
    signals: Optional[Dict[str, float]] = None
    veto: Optional[Dict[str, Any]] = None
    gates: Optional[List[Dict[str, Any]]] = None
    explanation: Optional[str] = None
    degraded: bool = False
    review_status: str = "PROPOSED"
    evidence: Optional[List[MatchEvidenceDTO]] = None
    fingerprints: Optional[Dict[str, Any]] = None
    review_details: Optional[Dict[str, Any]] = None
