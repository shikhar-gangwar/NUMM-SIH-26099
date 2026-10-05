from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.db.models import ImportBatch, Material, MaterialAttribute, Classification, Cpse, AppUser
from app.api.deps import get_current_user, require_role
from app.ingestion.service import IngestionService
from app.api.schemas.imports import ImportBatchDTO, ImportResultDTO
from app.api.schemas.material import MaterialDTO, AttributeValueDTO

router = APIRouter(prefix="/imports", tags=["Imports"])

@router.post("/upload", response_model=ImportResultDTO)
async def upload_import_file(
    file: UploadFile = File(...),
    cpse_code: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role(["DATA_STEWARD", "SUPER_ADMIN"]))
):
    if not file.filename or not file.filename.lower().endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Please upload a .csv or .xlsx file."
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    service = IngestionService(db)
    try:
        batch, row_reports = service.process_import(
            file_content=content,
            filename=file.filename,
            user=current_user,
            cpse_code_override=cpse_code
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )

    batch_dto = ImportBatchDTO(
        id=batch.id,
        cpse_id=batch.cpse_id,
        kind=batch.kind,
        filename=batch.filename,
        sha256=batch.sha256,
        total_rows=batch.total_rows,
        accepted_rows=batch.accepted_rows,
        rejected_rows=batch.rejected_rows,
        warning_rows=batch.warning_rows,
        status=batch.status,
        uploaded_by=batch.uploaded_by,
        created_at=batch.created_at
    )
    return ImportResultDTO(batch=batch_dto, row_reports=row_reports)

@router.get("/", response_model=List[ImportBatchDTO])
def list_import_batches(
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user)
):
    batches = db.query(ImportBatch).order_by(ImportBatch.created_at.desc()).all()
    return [
        ImportBatchDTO(
            id=b.id,
            cpse_id=b.cpse_id,
            kind=b.kind,
            filename=b.filename,
            sha256=b.sha256,
            total_rows=b.total_rows,
            accepted_rows=b.accepted_rows,
            rejected_rows=b.rejected_rows,
            warning_rows=b.warning_rows,
            status=b.status,
            uploaded_by=b.uploaded_by,
            created_at=b.created_at
        ) for b in batches
    ]

@router.get("/{batch_id}", response_model=ImportBatchDTO)
def get_import_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user)
):
    batch = db.query(ImportBatch).filter_by(id=batch_id).first()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import batch not found")
    return ImportBatchDTO(
        id=batch.id,
        cpse_id=batch.cpse_id,
        kind=batch.kind,
        filename=batch.filename,
        sha256=batch.sha256,
        total_rows=batch.total_rows,
        accepted_rows=batch.accepted_rows,
        rejected_rows=batch.rejected_rows,
        warning_rows=batch.warning_rows,
        status=batch.status,
        uploaded_by=batch.uploaded_by,
        created_at=batch.created_at
    )

@router.get("/{batch_id}/materials", response_model=List[MaterialDTO])
def get_batch_materials(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user)
):
    materials = db.query(Material).filter_by(batch_id=batch_id).all()
    results = []
    for m in materials:
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
        
        results.append(MaterialDTO(
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
            attributes=attr_dtos
        ))
    return results
