from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional, Dict, Any

from app.db.session import get_db
from app.db.models import Material, MaterialAttribute, Classification, Cpse, LegacyMapping, NationalMaterial, MaterialMatch, AuditEvent
from app.api.deps import require_role
from app.api.schemas.material import MaterialDTO, MaterialDetailDTO, AttributeValueDTO

router = APIRouter(prefix="/materials", tags=["Materials"])

def _build_material_dto(db: Session, m: Material) -> MaterialDTO:
    cpse = db.query(Cpse).filter_by(id=m.cpse_id).first()
    cpse_code = cpse.code if cpse else "UNKNOWN"

    cls_rec = db.query(Classification).filter_by(material_id=m.id, is_current=True).first()
    cat_code = cls_rec.category_code if cls_rec else "UNCLASSIFIED"
    cat_conf = cls_rec.confidence if cls_rec else 0.0

    attrs = db.query(MaterialAttribute).filter_by(material_id=m.id, is_current=True).all()
    attr_dtos = [
        AttributeValueDTO(
            key=a.key,
            raw_text=a.raw_text,
            value=a.value_text or a.value_num,
            unit=a.unit,
            canonical_value=a.canonical_value,
            source=a.source,
            confidence=a.confidence,
            span=a.span,
            rule_id=a.rule_id,
            assumed=a.assumed,
            internal_conflict=a.internal_conflict
        ) for a in attrs
    ]

    mapping = db.query(LegacyMapping).filter_by(material_id=m.id, status="ACTIVE").first()
    mapping_nmc = None
    if mapping:
        nat_mat = db.query(NationalMaterial).filter_by(uid=mapping.national_material_uid).first()
        mapping_nmc = nat_mat.nmc if nat_mat else mapping.national_material_uid

    return MaterialDTO(
        id=m.id,
        cpse_code=cpse_code,
        source_code=m.source_code,
        raw_description=m.raw_description,
        raw_uom=m.raw_uom,
        normalized_text=m.normalized_text,
        uom_canonical=m.uom_canonical,
        uom_dimension=m.uom_dimension,
        category_code=cat_code,
        category_confidence=cat_conf,
        attributes=attr_dtos,
        mapping_nmc=mapping_nmc,
        mapping_status=mapping.status if mapping else None,
        manufacturer=m.manufacturer,
        part_number=m.part_number,
        provenance=getattr(m, "provenance", "SYNTHETIC_DEMO"),
        provenance_metadata=getattr(m, "provenance_metadata", None),
        created_at=m.created_at,
        status=m.status
    )

@router.get("", response_model=List[MaterialDTO])
def list_materials(
    search: Optional[str] = None,
    cpse_code: Optional[str] = None,
    category_code: Optional[str] = None,
    provenance: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["VIEWER", "REVIEWER", "DATA_STEWARD", "SUPER_ADMIN"]))
):
    """
    Returns paginated materials with search and filtering by CPSE, Category, and Provenance.
    """
    query = db.query(Material).filter(Material.status == "ACTIVE")

    if cpse_code:
        cpse = db.query(Cpse).filter_by(code=cpse_code).first()
        if cpse:
            query = query.filter(Material.cpse_id == cpse.id)
        else:
            return []

    if category_code:
        query = query.join(Classification, Classification.material_id == Material.id).filter(
            Classification.category_code == category_code,
            Classification.is_current == True
        )

    if provenance:
        query = query.filter(Material.provenance == provenance)

    if search:
        s_clean = f"%{search.strip().upper()}%"
        query = query.filter(
            (Material.source_code.ilike(s_clean)) |
            (Material.raw_description.ilike(s_clean)) |
            (Material.normalized_text.ilike(s_clean))
        )

    offset = (page - 1) * page_size
    mats = query.order_by(Material.created_at.desc()).offset(offset).limit(page_size).all()
    return [_build_material_dto(db, m) for m in mats]

@router.get("/{id}", response_model=MaterialDetailDTO)
def get_material_by_id(
    id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["VIEWER", "REVIEWER", "DATA_STEWARD", "SUPER_ADMIN"]))
):
    """
    Returns a single material by ID with full technical provenance, match history, and audit timeline.
    """
    m = db.query(Material).filter_by(id=id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Material not found")
    
    base_dto = _build_material_dto(db, m)

    # 1. Fetch matches involving this material
    matches_q = db.query(MaterialMatch).filter(
        or_(MaterialMatch.material_a_id == m.id, MaterialMatch.material_b_id == m.id)
    ).order_by(MaterialMatch.created_at.desc())
    matches_count = matches_q.count()
    recent_matches_raw = matches_q.limit(10).all()

    recent_matches = []
    for match in recent_matches_raw:
        other_id = match.material_b_id if match.material_a_id == m.id else match.material_a_id
        other_mat = db.query(Material).filter_by(id=other_id).first()
        other_cpse = db.query(Cpse).filter_by(id=other_mat.cpse_id).first() if other_mat else None

        recent_matches.append({
            "match_id": match.id,
            "relationship": match.relationship,
            "equivalence_confidence": match.equivalence_confidence,
            "review_status": match.review_status,
            "veto_applied": bool(match.veto and match.veto.get("applied")),
            "veto_gate": match.veto.get("gate") if match.veto else None,
            "partner_material_id": other_id,
            "partner_cpse_code": other_cpse.code if other_cpse else "UNKNOWN",
            "partner_source_code": other_mat.source_code if other_mat else "UNKNOWN",
            "partner_raw_description": other_mat.raw_description if other_mat else "UNKNOWN",
            "created_at": match.created_at.isoformat() if match.created_at else None
        })

    # 2. Fetch audit trail for this material
    audits_raw = db.query(AuditEvent).filter(
        or_(
            AuditEvent.entity_id == m.id,
            AuditEvent.reason.ilike(f"%{m.source_code}%")
        )
    ).order_by(AuditEvent.created_at.desc()).limit(10).all()

    audit_events = [
        {
            "seq": a.seq,
            "action": a.action,
            "actor_role": a.actor_role,
            "timestamp": (a.ts or a.created_at).isoformat() if (a.ts or a.created_at) else None,
            "hash": a.hash,
            "reason": a.reason
        } for a in audits_raw
    ]


    return MaterialDetailDTO(
        **base_dto.model_dump(),
        matches_count=matches_count,
        recent_matches=recent_matches,
        audit_events=audit_events
    )

