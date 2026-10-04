from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class ReviewApproveRequestDTO(BaseModel):
    comment: Optional[str] = None

class ReviewRejectRequestDTO(BaseModel):
    reason_code: str
    comment: Optional[str] = None

class ReviewRemapRequestDTO(BaseModel):
    target_national_material_uid: str
    comment: Optional[str] = None

class ReviewResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    match_id: str
    status: str
    decision: str
    reviewer_id: str
    ai_relationship: str
    human_relationship: Optional[str] = None
    reason_code: Optional[str] = None
    comment: Optional[str] = None
    decided_at: datetime

class LegacyMappingDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    material_id: str
    national_material_uid: str
    cpse_code: Optional[str] = None
    cpse_name: Optional[str] = None
    source_code: Optional[str] = None
    raw_description: Optional[str] = None
    provenance: Optional[str] = None
    provenance_label: Optional[str] = None
    mapping_type: str
    status: str
    valid_from: datetime

class NationalMaterialResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: str
    nmc: str
    category_code: str
    status: str
    canonical_description: str
    sap_short_description: str
    spec_fingerprint: str
    current_version_no: int
    created_at: datetime
    cpse_count: int = 0
    legacy_mappings_count: int = 0
    legacy_mappings: List[LegacyMappingDTO] = []

class AnalyticsSummaryDTO(BaseModel):
    total_materials: int
    cpse_count: int
    match_runs_count: int
    potential_duplicates: int
    review_queue_count: int
    approved_count: int
    rejected_count: int
    national_materials_count: int
    legacy_mappings_count: int
    public_records_count: Optional[int] = 0
    controlled_demo_count: Optional[int] = 0
    synthetic_demo_count: Optional[int] = 0

class AnalyticsChartsDTO(BaseModel):
    materials_by_cpse: Dict[str, int]
    materials_by_category: Dict[str, int]
    relationship_distribution: Dict[str, int]
    review_status_distribution: Dict[str, int]
    confidence_histogram: Dict[str, int]
    veto_reasons_breakdown: Dict[str, int]
    materials_by_provenance: Optional[Dict[str, int]] = None
    mapping_coverage: Optional[Dict[str, Any]] = None

class ConsolidationOpportunityDTO(BaseModel):
    nmc: str
    canonical_description: str
    category_code: str
    cpse_count: int
    mapped_materials_count: int
    min_unit_price: float
    max_unit_price: float
    avg_unit_price: float
    estimated_annual_savings: float
    demonstration_flag: str = "Synthetic demonstration data"

class ProcurementAnalyticsDTO(BaseModel):
    cpse_sharing_nmc_count: int
    duplicate_materials_count: int
    mapping_coverage_pct: float
    unresolved_review_count: int
    unresolved_review_concentration: Dict[str, int]
    top_consolidation_opportunities: List[ConsolidationOpportunityDTO]
    demonstration_notes: str

