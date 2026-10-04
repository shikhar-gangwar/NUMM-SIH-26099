from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.db.models import NationalMaterial, LegacyMapping, Material, Cpse
from app.api.deps import require_role
from app.api.schemas.governance import NationalMaterialResponseDTO, LegacyMappingDTO

router = APIRouter(tags=["National Material Master & Legacy Mapping"])

def _to_legacy_dto(db: Session, leg: LegacyMapping) -> LegacyMappingDTO:
    mat = db.query(Material).filter_by(id=leg.material_id).first()
    cpse_code = "UNKNOWN"
    cpse_name = "Unknown CPSE"
    source_code = None
    raw_desc = None
    provenance = "CONTROLLED_GOLDEN_DEMO"
    provenance_label = "Synthetic demonstration record"
    if mat:
        source_code = mat.source_code
        raw_desc = mat.raw_description
        provenance = mat.provenance or "CONTROLLED_GOLDEN_DEMO"
        provenance_label = "Public-source record" if provenance == "REAL_PUBLIC" else "Synthetic demonstration record"
        cpse = db.query(Cpse).filter_by(id=mat.cpse_id).first()
        if cpse:
            cpse_code = cpse.code
            cpse_name = cpse.name

    return LegacyMappingDTO(
        id=leg.id,
        material_id=leg.material_id,
        national_material_uid=leg.national_material_uid,
        cpse_code=cpse_code,
        cpse_name=cpse_name,
        source_code=source_code,
        raw_description=raw_desc,
        provenance=provenance,
        provenance_label=provenance_label,
        mapping_type=leg.mapping_type,
        status=leg.status,
        valid_from=leg.valid_from
    )

@router.get("/national-materials", response_model=List[NationalMaterialResponseDTO])
def list_national_materials(
    category_code: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["VIEWER", "REVIEWER", "DATA_STEWARD", "SUPER_ADMIN"]))
):
    query = db.query(NationalMaterial).filter(NationalMaterial.status == "ACTIVE")
    if category_code:
        query = query.filter(NationalMaterial.category_code == category_code)
    if search:
        s_clean = f"%{search.strip().upper()}%"
        query = query.filter(
            (NationalMaterial.nmc.ilike(s_clean)) |
            (NationalMaterial.canonical_description.ilike(s_clean))
        )

    offset = (page - 1) * page_size
    items = query.order_by(NationalMaterial.created_at.desc()).offset(offset).limit(page_size).all()

    results = []
    for n in items:
        legs = db.query(LegacyMapping).filter_by(national_material_uid=n.uid, status="ACTIVE").all()
        leg_dtos = [_to_legacy_dto(db, l) for l in legs]
        unique_cpses = len(set(l.cpse_code for l in leg_dtos if l.cpse_code))
        results.append(
            NationalMaterialResponseDTO(
                uid=n.uid,
                nmc=n.nmc,
                category_code=n.category_code,
                status=n.status,
                canonical_description=n.canonical_description,
                sap_short_description=n.sap_short_description,
                spec_fingerprint=n.spec_fingerprint,
                current_version_no=n.current_version_no,
                created_at=n.created_at,
                cpse_count=unique_cpses,
                legacy_mappings_count=len(legs),
                legacy_mappings=leg_dtos
            )
        )
    return results

@router.get("/national-materials/{uid}", response_model=NationalMaterialResponseDTO)
def get_national_material(
    uid: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["VIEWER", "REVIEWER", "DATA_STEWARD", "SUPER_ADMIN"]))
):
    n = db.query(NationalMaterial).filter_by(uid=uid).first()
    if not n:
        # Try lookup by NMC string if uid is not UUID
        n = db.query(NationalMaterial).filter_by(nmc=uid).first()
        if not n:
            raise HTTPException(status_code=404, detail="National Material not found")

    legs = db.query(LegacyMapping).filter_by(national_material_uid=n.uid, status="ACTIVE").all()
    leg_dtos = [_to_legacy_dto(db, l) for l in legs]
    unique_cpses = len(set(l.cpse_code for l in leg_dtos if l.cpse_code))

    return NationalMaterialResponseDTO(
        uid=n.uid,
        nmc=n.nmc,
        category_code=n.category_code,
        status=n.status,
        canonical_description=n.canonical_description,
        sap_short_description=n.sap_short_description,
        spec_fingerprint=n.spec_fingerprint,
        current_version_no=n.current_version_no,
        created_at=n.created_at,
        cpse_count=unique_cpses,
        legacy_mappings_count=len(legs),
        legacy_mappings=leg_dtos
    )

@router.get("/legacy-mappings", response_model=List[LegacyMappingDTO])
def list_legacy_mappings(
    cpse_code: Optional[str] = None,
    nmc: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["VIEWER", "REVIEWER", "DATA_STEWARD", "SUPER_ADMIN"]))
):
    query = db.query(LegacyMapping).filter(LegacyMapping.status == "ACTIVE")
    if nmc:
        nat = db.query(NationalMaterial).filter_by(nmc=nmc).first()
        if nat:
            query = query.filter(LegacyMapping.national_material_uid == nat.uid)

    offset = (page - 1) * page_size
    legs = query.order_by(LegacyMapping.created_at.desc()).offset(offset).limit(page_size).all()

    results = []
    for l in legs:
        dto = _to_legacy_dto(db, l)
        if cpse_code and dto.cpse_code != cpse_code:
            continue
        results.append(dto)

    return results
