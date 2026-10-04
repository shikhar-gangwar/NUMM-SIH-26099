from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime

class AttributeValueDTO(BaseModel):
    key: str
    raw_text: Optional[str] = None
    value: Optional[Any] = None
    unit: Optional[str] = None
    canonical_value: Optional[Any] = None
    source: str # STRUCTURED, RULE, LLM, REVIEWER
    confidence: float = 1.0
    span: Optional[List[int]] = None
    rule_id: Optional[str] = None
    assumed: bool = False
    internal_conflict: bool = False

class MaterialDTO(BaseModel):
    id: str
    cpse_code: str
    source_code: str
    raw_description: str
    raw_uom: str
    normalized_text: Optional[str] = None
    uom_canonical: Optional[str] = None
    uom_dimension: Optional[str] = None
    category_code: Optional[str] = None
    category_confidence: Optional[float] = None
    attributes: List[AttributeValueDTO] = []
    mapping_nmc: Optional[str] = None
    mapping_status: Optional[str] = None
    manufacturer: Optional[str] = None
    part_number: Optional[str] = None
    provenance: Optional[str] = "SYNTHETIC_DEMO"
    provenance_metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    status: Optional[str] = "ACTIVE"

class MaterialDetailDTO(MaterialDTO):
    matches_count: int = 0
    recent_matches: List[Dict[str, Any]] = []
    audit_events: List[Dict[str, Any]] = []

