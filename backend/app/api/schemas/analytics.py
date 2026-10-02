from pydantic import BaseModel
from typing import Optional, Dict, Any

class AnalyticsSummaryDTO(BaseModel):
    total_source_materials: int
    canonical_national_materials: int
    duplicate_candidates: int
    confirmed_duplicates: int
    equivalent_materials: int
    unresolved_records: int
    review_queue_size: int
    approval_rate: float
    rejection_rate: float
    cross_cpse_materials: int
    consolidation_ratio: float
    data_quality_score: float
    procurement_aggregation_opportunity: float
    vetoed_pairs_count: int
    as_of: str
