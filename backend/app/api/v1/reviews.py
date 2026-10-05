from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.db.session import get_db
from app.db.models import MaterialMatch, Material, Classification, Cpse, Review, MatchEvidence, AppUser, NationalMaterial, LegacyMapping
from app.api.deps import require_role
from app.api.schemas.match import PairResultDTO, MatchEvidenceDTO
from app.api.schemas.material import MaterialDTO, AttributeValueDTO
from app.api.schemas.governance import (
    ReviewApproveRequestDTO, ReviewRejectRequestDTO, ReviewRemapRequestDTO, ReviewResponseDTO, NationalMaterialResponseDTO
)
from app.governance.service import GovernanceService
from app.api.v1.matching import _to_material_dto

router = APIRouter(tags=["Governance & Review Workflow"])

def _build_review_details(db: Session, match_id: str) -> Optional[Dict[str, Any]]:
    rev = db.query(Review).filter_by(match_id=match_id).order_by(Review.created_at.desc()).first()
    if not rev:
        return None
    user = db.query(AppUser).filter_by(id=rev.reviewer_id).first()
    
    # Check if an NMC was linked via LegacyMapping
    leg = db.query(LegacyMapping).filter_by(review_id=match_id).first()
    target_nmc = None
    if leg:
        nat = db.query(NationalMaterial).filter_by(uid=leg.national_material_uid).first()
        if nat:
            target_nmc = nat.nmc

    return {
        "decision": rev.decision,
        "decided_by": user.username if user else "steward_admin",
        "role": user.role if user else "SUPER_ADMIN",
        "decided_at": rev.decided_at.isoformat() if rev.decided_at else None,
        "reason_code": rev.reason_code,
        "comment": rev.comment,
        "target_nmc": target_nmc
    }

@router.get("/reviews/summary/counts")
def get_review_counts(
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["VIEWER", "REVIEWER", "DATA_STEWARD", "SUPER_ADMIN"]))
):
    """
    Returns total counts across review queue status buckets for dashboard and filter chips.
    """
    base_q = db.query(MaterialMatch).filter(MaterialMatch.review_status == "PROPOSED")
    total = base_q.count()
    conflict_count = base_q.filter(MaterialMatch.relationship == "NOT_EQUIVALENT").count()
    unknown_count = base_q.filter(MaterialMatch.relationship == "REVIEW_REQUIRED").count()
    safe_count = base_q.filter(MaterialMatch.relationship.in_(["FUNCTIONALLY_EQUIVALENT", "NEAR_DUPLICATE", "EXACT_DUPLICATE"])).count()
    low_conf_count = base_q.filter(MaterialMatch.relationship.in_(["RELATED", "COMPATIBLE"])).count()

    return {
        "total": total,
        "conflict": conflict_count,
        "unknown": unknown_count,
        "safe_equiv": safe_count,
        "low_conf": low_conf_count
    }

@router.get("/reviews", response_model=List[PairResultDTO])
def list_review_queue(
    review_status: Optional[str] = Query("PROPOSED"),
    category: Optional[str] = None,
    relationship: Optional[str] = None,
    cpse_code: Optional[str] = None,
    has_veto: Optional[bool] = None,
    min_confidence: Optional[float] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(60, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["VIEWER", "REVIEWER", "DATA_STEWARD", "SUPER_ADMIN"]))
):
    """
    Returns paginated match pairs in the governance review queue with rich filtering.
    """
    query = db.query(MaterialMatch)
    if review_status and review_status != "ALL":
        query = query.filter(MaterialMatch.review_status == review_status)
    if relationship:
        query = query.filter(MaterialMatch.relationship == relationship)
    if min_confidence is not None:
        query = query.filter(MaterialMatch.equivalence_confidence >= min_confidence)

    # When no specific filters are requested on page 1, provide a balanced, diverse
    # governance queue displaying all 4 critical categories
    if not relationship and not search and not category and not cpse_code and has_veto is None and page == 1:
        # Prioritize controlled golden demo matches first for competition walkthrough
        golden_matches = query.join(
            Material, Material.id == MaterialMatch.material_a_id
        ).filter(Material.provenance == "CONTROLLED_GOLDEN_DEMO").order_by(MaterialMatch.created_at.desc()).limit(30).all()

        bucket_size = max(15, page_size // 4)
        safe_m = query.filter(MaterialMatch.relationship.in_(["FUNCTIONALLY_EQUIVALENT", "NEAR_DUPLICATE", "EXACT_DUPLICATE"])).order_by(MaterialMatch.equivalence_confidence.desc()).limit(bucket_size).all()
        conflict_m = query.filter(MaterialMatch.relationship == "NOT_EQUIVALENT").order_by(MaterialMatch.raw_score.desc()).limit(bucket_size).all()
        unknown_m = query.filter(MaterialMatch.relationship == "REVIEW_REQUIRED").order_by(MaterialMatch.raw_score.desc()).limit(bucket_size).all()
        low_conf_m = query.filter(MaterialMatch.relationship.in_(["RELATED", "COMPATIBLE"])).order_by(MaterialMatch.raw_score.desc()).limit(bucket_size).all()

        seen_ids = set()
        ordered_matches = []
        
        # Interleave golden matches: Safe -> Conflict (G2) -> Review (G4)
        g_safe = [m for m in golden_matches if m.relationship in ["FUNCTIONALLY_EQUIVALENT", "EXACT_DUPLICATE", "NEAR_DUPLICATE"]]
        g_conf = [m for m in golden_matches if m.relationship == "NOT_EQUIVALENT"]
        g_rev = [m for m in golden_matches if m.relationship == "REVIEW_REQUIRED"]
        
        max_g = max(len(g_safe), len(g_conf), len(g_rev)) if golden_matches else 0
        for i in range(max_g):
            if i < len(g_safe) and g_safe[i].id not in seen_ids:
                seen_ids.add(g_safe[i].id)
                ordered_matches.append(g_safe[i])
            if i < len(g_conf) and g_conf[i].id not in seen_ids:
                seen_ids.add(g_conf[i].id)
                ordered_matches.append(g_conf[i])
            if i < len(g_rev) and g_rev[i].id not in seen_ids:
                seen_ids.add(g_rev[i].id)
                ordered_matches.append(g_rev[i])

        max_b = max(len(safe_m), len(conflict_m), len(unknown_m), len(low_conf_m))
        for i in range(max_b):
            for b in [safe_m, conflict_m, unknown_m, low_conf_m]:
                if i < len(b) and b[i].id not in seen_ids:
                    seen_ids.add(b[i].id)
                    ordered_matches.append(b[i])
        matches = ordered_matches
    else:
        offset = (page - 1) * page_size
        matches = query.order_by(MaterialMatch.created_at.desc()).offset(offset).limit(page_size * 2).all()

    results = []
    for m in matches:
        if len(results) >= page_size:
            break

        if has_veto is True and not (m.veto and m.veto.get("applied")):
            continue
        if has_veto is False and (m.veto and m.veto.get("applied")):
            continue

        mat_a = db.query(Material).filter_by(id=m.material_a_id).first()
        mat_b = db.query(Material).filter_by(id=m.material_b_id).first()
        if not mat_a or not mat_b:
            continue

        if cpse_code:
            cpse_a = db.query(Cpse).filter_by(id=mat_a.cpse_id).first()
            cpse_b = db.query(Cpse).filter_by(id=mat_b.cpse_id).first()
            if (not cpse_a or cpse_a.code != cpse_code) and (not cpse_b or cpse_b.code != cpse_code):
                continue

        if category:
            cls_a = db.query(Classification).filter_by(material_id=mat_a.id, is_current=True).first()
            if not cls_a or cls_a.category_code != category:
                continue

        if search:
            search_clean = search.strip().upper()
            txt_a = (mat_a.normalized_text or mat_a.raw_description or "").upper()
            txt_b = (mat_b.normalized_text or mat_b.raw_description or "").upper()
            code_a = (mat_a.source_code or "").upper()
            code_b = (mat_b.source_code or "").upper()
            if search_clean not in txt_a and search_clean not in txt_b and search_clean not in code_a and search_clean not in code_b:
                continue

        ev_rows = db.query(MatchEvidence).filter_by(match_id=m.id).all()
        ev_dtos = [
            MatchEvidenceDTO(
                id=e.id,
                match_id=e.match_id,
                kind=e.kind,
                payload=e.payload,
                score=e.score,
                verdict=e.verdict
            ) for e in ev_rows
        ]

        results.append(
            PairResultDTO(
                id=m.id,
                run_id=m.run_id,
                material_a=_to_material_dto(db, mat_a),
                material_b=_to_material_dto(db, mat_b),
                relationship=m.relationship,
                equivalence_confidence=m.equivalence_confidence,
                raw_score=m.raw_score,
                signals=m.signals,
                veto=m.veto,
                gates=m.gates,
                explanation=m.explanation,
                degraded=m.degraded,
                review_status=m.review_status,
                evidence=ev_dtos,
                fingerprints={"ruleset": "v1"},
                review_details=_build_review_details(db, m.id) if m.review_status not in ["PROPOSED", "PENDING"] else None
            )
        )

    return results

@router.get("/reviews/{match_id}", response_model=PairResultDTO)
def get_review_detail(
    match_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["VIEWER", "REVIEWER", "DATA_STEWARD", "SUPER_ADMIN"]))
):
    m = db.query(MaterialMatch).filter_by(id=match_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Match pair not found")

    mat_a = db.query(Material).filter_by(id=m.material_a_id).first()
    mat_b = db.query(Material).filter_by(id=m.material_b_id).first()
    if not mat_a or not mat_b:
        raise HTTPException(status_code=404, detail="Material entities not found")

    ev_rows = db.query(MatchEvidence).filter_by(match_id=m.id).all()
    ev_dtos = [
        MatchEvidenceDTO(
            id=e.id,
            match_id=e.match_id,
            kind=e.kind,
            payload=e.payload,
            score=e.score,
            verdict=e.verdict
        ) for e in ev_rows
    ]

    return PairResultDTO(
        id=m.id,
        run_id=m.run_id,
        material_a=_to_material_dto(db, mat_a),
        material_b=_to_material_dto(db, mat_b),
        relationship=m.relationship,
        equivalence_confidence=m.equivalence_confidence,
        raw_score=m.raw_score,
        signals=m.signals,
        veto=m.veto,
        gates=m.gates,
        explanation=m.explanation,
        degraded=m.degraded,
        review_status=m.review_status,
        evidence=ev_dtos,
        fingerprints={"ruleset": "v1"},
        review_details=_build_review_details(db, m.id)
    )

@router.post("/reviews/{match_id}/approve", response_model=ReviewResponseDTO, status_code=status.HTTP_200_OK)
def approve_match(
    match_id: str,
    req: ReviewApproveRequestDTO = ReviewApproveRequestDTO(),
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["DATA_STEWARD", "SUPER_ADMIN"]))
):
    """
    Approves match pair equivalence, creating/linking National Material Code and legacy mappings.
    Protected: Only DATA_STEWARD and SUPER_ADMIN may approve.
    """
    review_row, nat_mat, mappings = GovernanceService.approve_match_pair(
        db=db,
        match_id=match_id,
        user_id=current_user.id,
        comment=req.comment
    )
    return ReviewResponseDTO.model_validate(review_row)

@router.post("/reviews/{match_id}/reject", response_model=ReviewResponseDTO, status_code=status.HTTP_200_OK)
def reject_match(
    match_id: str,
    req: ReviewRejectRequestDTO,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["DATA_STEWARD", "SUPER_ADMIN"]))
):
    """
    Rejects candidate match pair equivalence with mandatory reason code.
    Protected: Only DATA_STEWARD and SUPER_ADMIN may reject.
    """
    review_row = GovernanceService.reject_match_pair(
        db=db,
        match_id=match_id,
        user_id=current_user.id,
        reason_code=req.reason_code,
        comment=req.comment
    )
    return ReviewResponseDTO.model_validate(review_row)

@router.post("/reviews/{match_id}/remap", response_model=ReviewResponseDTO, status_code=status.HTTP_200_OK)
def remap_match(
    match_id: str,
    req: ReviewRemapRequestDTO,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["DATA_STEWARD", "SUPER_ADMIN"]))
):
    """
    Remaps candidate material to an existing National Material Code.
    Protected: Only DATA_STEWARD and SUPER_ADMIN may remap.
    """
    review_row, leg_mapping = GovernanceService.remap_material(
        db=db,
        match_id=match_id,
        target_national_uid=req.target_national_material_uid,
        user_id=current_user.id,
        reason=req.comment
    )
    return ReviewResponseDTO.model_validate(review_row)
