import os
import io
import hashlib
import pandas as pd
from typing import BinaryIO
from sqlalchemy.orm import Session
from app.db.models import Cpse, ImportBatch, Material, MaterialAttribute, Classification, AppUser
from app.normalization.uom import normalize_uom
from app.normalization.text import normalize_text
from app.extraction.extractor import detect_category, extract_attributes
from app.audit.service import AuditService

def compute_file_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def normalize_header(col: str) -> str:
    c = str(col).strip().lower().replace(" ", "_").replace("-", "_")
    if c in ["source_code", "material_code", "code", "item_code", "mat_code"]:
        return "source_material_code"
    if c in ["desc", "raw_description", "item_description", "material_description"]:
        return "description"
    if c in ["unit", "unit_of_measure", "uom_code"]:
        return "uom"
    if c in ["cpse", "cpse_name", "company"]:
        return "cpse_code"
    if c in ["cat_hint", "group", "category"]:
        return "category_hint"
    if c in ["mfg", "make"]:
        return "manufacturer"
    if c in ["part_no", "partnum", "part_number"]:
        return "part_number"
    return c

class IngestionService:
    def __init__(self, db: Session):
        self.db = db

    def process_import(
        self,
        file_content: bytes,
        filename: str,
        user: AppUser,
        cpse_code_override: str | None = None
    ) -> tuple[ImportBatch, list[dict]]:
        """
        Parses CSV or XLSX file, validates records, creates ImportBatch, inserts Material and MaterialAttribute rows.
        """
        sha256_hash = compute_file_sha256(file_content)
        
        # Determine CPSE
        cpse = None
        if cpse_code_override:
            cpse = self.db.query(Cpse).filter_by(code=cpse_code_override).first()
        if not cpse and user.cpse_id:
            cpse = self.db.query(Cpse).filter_by(id=user.cpse_id).first()
        if not cpse:
            # Fallback to default/first CPSE or create default dev CPSE
            cpse = self.db.query(Cpse).first()
            if not cpse:
                cpse = Cpse(code="CPSE-A", name="CPSE-A (Thermal Power Demo)", sector="Energy", is_synthetic=True)
                self.db.add(cpse)
                self.db.flush()

        # Parse file into pandas DataFrame
        ext = os.path.splitext(filename)[1].lower()
        try:
            if ext in [".xlsx", ".xls"]:
                df = pd.read_excel(io.BytesIO(file_content))
            else:
                df = pd.read_csv(io.BytesIO(file_content), dtype=str)
        except Exception as e:
            raise ValueError(f"Failed to parse file format ({ext}): {e}")

        # Normalize column headers
        df.columns = [normalize_header(c) for c in df.columns]
        
        required_cols = ["source_material_code", "description"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column '{col}' in input file. Found columns: {list(df.columns)}")

        if "uom" not in df.columns:
            df["uom"] = "EA"

        # Create ImportBatch record
        batch = ImportBatch(
            cpse_id=cpse.id,
            kind="MATERIAL",
            filename=filename,
            sha256=sha256_hash,
            total_rows=len(df),
            accepted_rows=0,
            rejected_rows=0,
            warning_rows=0,
            status="PROCESSING",
            uploaded_by=user.id
        )
        self.db.add(batch)
        self.db.flush()

        row_reports = []
        seen_codes = set()

        for idx, row in df.iterrows():
            row_num = idx + 2 # 1-based index including header
            
            raw_code = str(row.get("source_material_code", "")).strip()
            raw_desc = str(row.get("description", "")).strip()
            raw_uom = str(row.get("uom", "EA")).strip()
            cat_hint = str(row.get("category_hint", "")).strip() if pd.notna(row.get("category_hint")) else None
            mfg = str(row.get("manufacturer", "")).strip() if pd.notna(row.get("manufacturer")) else None
            part_no = str(row.get("part_number", "")).strip() if pd.notna(row.get("part_number")) else None

            # Validation: empty required fields
            if not raw_code or not raw_desc or raw_code.lower() == "nan" or raw_desc.lower() == "nan":
                batch.rejected_rows += 1
                row_reports.append({"row": row_num, "status": "REJECTED", "error": "Missing source_material_code or description"})
                continue

            # Validation: duplicate code in file
            if raw_code in seen_codes:
                batch.warning_rows += 1
                row_reports.append({"row": row_num, "status": "WARNING", "message": f"Duplicate code '{raw_code}' in file, skipped duplicate"})
                continue
            seen_codes.add(raw_code)

            # Check if material code already exists in DB for this CPSE
            existing = self.db.query(Material).filter_by(cpse_id=cpse.id, source_code=raw_code).first()
            if existing:
                batch.warning_rows += 1
                row_reports.append({"row": row_num, "status": "SKIPPED", "message": f"Material '{raw_code}' already exists in database"})
                continue

            # Normalization
            canon_uom, uom_dim, uom_flags = normalize_uom(raw_uom)
            norm_res = normalize_text(raw_desc)

            if uom_flags:
                batch.warning_rows += 1

            # Detect Category & Extract Attributes
            cat_code = detect_category(norm_res.text, hint=cat_hint)
            extracted_attrs = extract_attributes(norm_res.text, cat_code, manufacturer=mfg, part_number=part_no)

            # Create Material record
            mat = Material(
                cpse_id=cpse.id,
                source_code=raw_code,
                raw_description=raw_desc,
                raw_uom=raw_uom,
                category_hint=cat_hint,
                manufacturer=mfg,
                part_number=part_no,
                batch_id=batch.id,
                normalized_text=norm_res.text,
                uom_canonical=canon_uom,
                uom_dimension=uom_dim,
                norm_flags=norm_res.flags + uom_flags,
                status="ACTIVE"
            )
            self.db.add(mat)
            self.db.flush()

            # Create Classification record
            cls_rec = Classification(
                material_id=mat.id,
                category_code=cat_code,
                confidence=1.0 if cat_code != "UNCLASSIFIED" else 0.5,
                method="RULE",
                input_hash=hashlib.sha256(norm_res.text.encode("utf-8")).hexdigest(),
                is_current=True
            )
            self.db.add(cls_rec)

            # Create MaterialAttribute records
            for ea in extracted_attrs:
                mat_attr = MaterialAttribute(
                    material_id=mat.id,
                    key=ea.key,
                    raw_text=ea.raw_text,
                    value_text=ea.value_text,
                    value_num=ea.value_num,
                    unit=ea.unit,
                    canonical_value=ea.canonical_value,
                    source=ea.source,
                    confidence=ea.confidence,
                    assumed=ea.assumed,
                    internal_conflict=ea.internal_conflict,
                    rule_id=ea.rule_id,
                    is_current=True
                )
                self.db.add(mat_attr)

            batch.accepted_rows += 1
            row_reports.append({"row": row_num, "status": "ACCEPTED", "source_code": raw_code, "category": cat_code})

        batch.status = "COMPLETED" if batch.rejected_rows == 0 else "COMPLETED_WITH_ERRORS"
        
        # Record audit log
        AuditService.record(
            db=self.db,
            actor_id=user.id,
            actor_role=user.role,
            action="IMPORT_BATCH_CREATED",
            entity_type="IMPORT_BATCH",
            entity_id=batch.id,
            after={
                "filename": filename,
                "total_rows": batch.total_rows,
                "accepted_rows": batch.accepted_rows,
                "rejected_rows": batch.rejected_rows,
                "status": batch.status
            }
        )
        self.db.commit()
        self.db.refresh(batch)
        
        return batch, row_reports
