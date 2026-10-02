from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.api.schemas.material import MaterialDTO

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
    fingerprints: Optional[Dict[str, Any]] = None
