from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class LegacyMappingDTO(BaseModel):
    cpse: str
    source_code: str
    raw_description: str
    mapped_on: str
    mapping_type: str
    review_id: Optional[str] = None

class NationalMaterialDTO(BaseModel):
    uid: str
    nmc: str
    category_code: str
    status: str
    canonical_description: str
    sap_short_description: str
    attributes: Dict[str, Any]
    version_no: int
    legacy: List[LegacyMappingDTO] = []
    procurement_summary: Optional[Dict[str, Any]] = None
