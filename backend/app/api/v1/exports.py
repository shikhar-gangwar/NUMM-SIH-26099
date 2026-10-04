from typing import Optional
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
import csv
import io
from datetime import datetime, timezone

from app.db.session import get_db
from app.db.models import LegacyMapping, NationalMaterial, Material, Cpse
from app.api.deps import require_role

router = APIRouter(tags=["Exports"])

@router.get("/exports/crosswalk.csv")
def export_crosswalk_csv(
    nmc: Optional[str] = None,
    category_code: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["VIEWER", "REVIEWER", "DATA_STEWARD", "SUPER_ADMIN"]))
):
    """
    Exports all active CPSE-to-NMC legacy mappings as a CSV file.
    Supports optional filtering by NMC or Category Code.
    """
    query = (
        db.query(LegacyMapping)
        .filter(LegacyMapping.status == "ACTIVE")
    )
    if nmc or category_code:
        query = query.join(NationalMaterial, LegacyMapping.national_material_uid == NationalMaterial.uid)
        if nmc:
            query = query.filter(NationalMaterial.nmc.ilike(f"%{nmc.strip()}%"))
        if category_code:
            query = query.filter(NationalMaterial.category_code == category_code.strip())

    mappings = query.order_by(LegacyMapping.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "NMC",
        "National_UID",
        "CPSE_Code",
        "Source_Material_Code",
        "Raw_Description",
        "Canonical_Description",
        "Category",
        "Mapped_On",
        "Status"
    ])

    for leg in mappings:
        nat = db.query(NationalMaterial).filter_by(uid=leg.national_material_uid).first()
        mat = db.query(Material).filter_by(id=leg.material_id).first()
        cpse_code = "UNKNOWN"
        source_code = ""
        raw_desc = ""
        category_code_val = ""
        canonical_desc = ""
        nmc_val = ""

        if nat:
            nmc_val = nat.nmc
            category_code_val = nat.category_code
            canonical_desc = nat.canonical_description

        if mat:
            source_code = mat.source_code or ""
            raw_desc = mat.raw_description or ""
            cpse = db.query(Cpse).filter_by(id=mat.cpse_id).first()
            if cpse:
                cpse_code = cpse.code

        writer.writerow([
            nmc_val,
            leg.national_material_uid,
            cpse_code,
            source_code,
            raw_desc,
            canonical_desc,
            category_code_val,
            leg.valid_from.isoformat() if leg.valid_from else "",
            leg.status
        ])

    csv_content = output.getvalue()
    ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    if nmc:
        clean_nmc = nmc.replace("-", "_").replace(" ", "")
        filename = f"crosswalk_{clean_nmc}_{ts}.csv"
    elif category_code:
        filename = f"crosswalk_{category_code.lower()}_{ts}.csv"
    else:
        filename = f"national_material_crosswalk_{ts}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )

