import hashlib
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.models import (
    MaterialMatch, Material, Classification, MaterialAttribute,
    NationalMaterial, NationalMaterialVersion, LegacyMapping, Review, AppUser
)
from app.governance.nmc import generate_nmc, compute_spec_fingerprint
from app.audit.service import AuditService
from app.core.ids import generate_uuidv7
from app.core.errors import BadRequestException, NotFoundException, ConflictException

class GovernanceService:
    @staticmethod
    def _get_material_attributes_dict(db: Session, material_id: str) -> list[dict]:
        attrs = db.query(MaterialAttribute).filter_by(material_id=material_id, is_current=True).all()
        return [
            {
                "key": a.key,
                "raw_text": a.raw_text,
                "value_text": a.value_text,
                "value_num": a.value_num,
                "canonical_value": a.canonical_value,
                "unit": a.unit
            } for a in attrs
        ]

    @staticmethod
    def _build_sap_short_description(norm_text: str, category_code: str) -> str:
        """
        Formats SAP short description <= 40 characters.
        """
        clean = norm_text.strip().upper()
        if len(clean) <= 40:
            return clean
        # Truncate deterministically
        return clean[:37] + "..."

    @classmethod
    def approve_match_pair(
        cls,
        db: Session,
        match_id: str,
        user_id: str,
        comment: str | None = None
    ) -> tuple[Review, NationalMaterial, list[LegacyMapping]]:
        """
        Approves a candidate match pair in a single atomic database transaction.
        Creates or links to a NationalMaterial and creates LegacyMapping entries for both CPSE materials.
        """
        match = db.query(MaterialMatch).filter_by(id=match_id).first()
        if not match:
            raise NotFoundException(f"Match record '{match_id}' not found")
        
        if match.review_status == "APPROVED":
            # Already approved; return existing review & national material
            existing_rev = db.query(Review).filter_by(match_id=match_id, decision="APPROVE").first()
            leg_a = db.query(LegacyMapping).filter_by(material_id=match.material_a_id, status="ACTIVE").first()
            if leg_a:
                nat = db.query(NationalMaterial).filter_by(uid=leg_a.national_material_uid).first()
                legs = db.query(LegacyMapping).filter_by(national_material_uid=nat.uid).all()
                return existing_rev, nat, legs

        mat_a = db.query(Material).filter_by(id=match.material_a_id).first()
        mat_b = db.query(Material).filter_by(id=match.material_b_id).first()
        if not mat_a or not mat_b:
            raise NotFoundException("Material entities not found for match pair")

        cls_a = db.query(Classification).filter_by(material_id=mat_a.id, is_current=True).first()
        category_code = cls_a.category_code if cls_a else "UNCLASSIFIED"

        attrs_a = cls._get_material_attributes_dict(db, mat_a.id)
        spec_fp = compute_spec_fingerprint(category_code, attrs_a)

        # 1. Check existing LegacyMapping for Material A or Material B
        leg_a = db.query(LegacyMapping).filter_by(material_id=mat_a.id, status="ACTIVE").first()
        leg_b = db.query(LegacyMapping).filter_by(material_id=mat_b.id, status="ACTIVE").first()

        nat_mat = None

        if leg_a:
            nat_mat = db.query(NationalMaterial).filter_by(uid=leg_a.national_material_uid).first()
        elif leg_b:
            nat_mat = db.query(NationalMaterial).filter_by(uid=leg_b.national_material_uid).first()
        
        # 2. Spec-fingerprint guard: check if an active NationalMaterial already has this spec_fingerprint
        if not nat_mat:
            existing_fp_mat = db.query(NationalMaterial).filter_by(
                category_code=category_code,
                spec_fingerprint=spec_fp,
                status="ACTIVE"
            ).first()
            if existing_fp_mat:
                nat_mat = existing_fp_mat

        # 3. Create new NationalMaterial if none exists
        if not nat_mat:
            nmc_code = generate_nmc(db, category_code)
            sap_short = cls._build_sap_short_description(mat_a.normalized_text or mat_a.raw_description, category_code)
            
            nat_mat = NationalMaterial(
                uid=str(generate_uuidv7()),
                nmc=nmc_code,
                category_code=category_code,
                status="ACTIVE",
                canonical_description=mat_a.normalized_text or mat_a.raw_description,
                sap_short_description=sap_short,
                spec_fingerprint=spec_fp,
                current_version_no=1,
                created_by_review_id=match_id
            )
            db.add(nat_mat)
            db.flush()

            # Record initial NationalMaterialVersion
            version_row = NationalMaterialVersion(
                uid=nat_mat.uid,
                version_no=1,
                attributes=attrs_a,
                canonical_description=nat_mat.canonical_description,
                fingerprint=spec_fp,
                changed_by=user_id,
                reason="Initial creation from steward review approval"
            )
            db.add(version_row)

        # 4. Create or activate LegacyMapping rows for both materials
        mappings = []
        for mat in [mat_a, mat_b]:
            existing_leg = db.query(LegacyMapping).filter_by(
                material_id=mat.id,
                national_material_uid=nat_mat.uid,
                status="ACTIVE"
            ).first()
            if not existing_leg:
                leg_row = LegacyMapping(
                    id=str(generate_uuidv7()),
                    material_id=mat.id,
                    national_material_uid=nat_mat.uid,
                    mapping_type="FUNCTIONAL" if match.relationship == "FUNCTIONALLY_EQUIVALENT" else "EXACT",
                    status="ACTIVE",
                    review_id=match_id
                )
                db.add(leg_row)
                mappings.append(leg_row)
            else:
                mappings.append(existing_leg)

        # 5. Update MaterialMatch review status
        old_status = match.review_status
        match.review_status = "APPROVED"
        db.add(match)

        # 6. Create Review record
        review_row = Review(
            id=str(generate_uuidv7()),
            match_id=match_id,
            status="APPROVED",
            decision="APPROVE",
            reviewer_id=user_id,
            ai_relationship=match.relationship,
            human_relationship="FUNCTIONALLY_EQUIVALENT",
            reason_code="VERIFIED_EQUIVALENCE",
            comment=comment,
            evidence_snapshot={"signals": match.signals, "veto": match.veto}
        )
        db.add(review_row)
        db.commit()

        # 7. Append-only Audit Log
        AuditService.record(
            db=db,
            actor_role="DATA_STEWARD",
            action="REVIEW_APPROVED",
            entity_type="material_match",
            entity_id=match_id,
            actor_id=user_id,
            before={"review_status": old_status},
            after={"review_status": "APPROVED", "nmc": nat_mat.nmc, "national_uid": nat_mat.uid},
            reason=f"Approved match pair {mat_a.source_code} <-> {mat_b.source_code}, assigned NMC {nat_mat.nmc}."
        )

        return review_row, nat_mat, mappings

    @classmethod
    def reject_match_pair(
        cls,
        db: Session,
        match_id: str,
        user_id: str,
        reason_code: str,
        comment: str | None = None
    ) -> Review:
        """
        Rejects a candidate match pair and records steward rejection reason.
        """
        match = db.query(MaterialMatch).filter_by(id=match_id).first()
        if not match:
            raise NotFoundException(f"Match record '{match_id}' not found")

        old_status = match.review_status
        match.review_status = "REJECTED"
        db.add(match)

        review_row = Review(
            id=str(generate_uuidv7()),
            match_id=match_id,
            status="REJECTED",
            decision="REJECT",
            reviewer_id=user_id,
            ai_relationship=match.relationship,
            human_relationship="NOT_EQUIVALENT",
            reason_code=reason_code or "TECHNICAL_MISMATCH",
            comment=comment,
            evidence_snapshot={"signals": match.signals, "veto": match.veto}
        )
        db.add(review_row)
        db.commit()

        AuditService.record(
            db=db,
            actor_role="DATA_STEWARD",
            action="REVIEW_REJECTED",
            entity_type="material_match",
            entity_id=match_id,
            actor_id=user_id,
            before={"review_status": old_status},
            after={"review_status": "REJECTED", "reason_code": reason_code},
            reason=f"Rejected match pair. Reason: {reason_code}. Comment: {comment or 'None'}"
        )

        return review_row

    @classmethod
    def remap_material(
        cls,
        db: Session,
        match_id: str,
        target_national_uid: str,
        user_id: str,
        reason: str | None = None
    ) -> tuple[Review, LegacyMapping]:
        """
        Remaps material pair to a specified target NationalMaterial UID.
        """
        match = db.query(MaterialMatch).filter_by(id=match_id).first()
        if not match:
            raise NotFoundException(f"Match record '{match_id}' not found")

        nat_mat = db.query(NationalMaterial).filter_by(uid=target_national_uid).first()
        if not nat_mat:
            raise NotFoundException(f"Target National Material '{target_national_uid}' not found")

        mat_a = db.query(Material).filter_by(id=match.material_a_id).first()
        
        # Deactivate old mapping if any
        existing_leg = db.query(LegacyMapping).filter_by(material_id=mat_a.id, status="ACTIVE").first()
        if existing_leg:
            existing_leg.status = "CLOSED"
            existing_leg.valid_to = datetime.now(timezone.utc)
            existing_leg.closed_reason = "Remapped to different National Material"
            db.add(existing_leg)

        leg_row = LegacyMapping(
            id=str(generate_uuidv7()),
            material_id=mat_a.id,
            national_material_uid=nat_mat.uid,
            mapping_type="MANUAL",
            status="ACTIVE",
            review_id=match_id
        )
        db.add(leg_row)

        old_status = match.review_status
        match.review_status = "APPROVED"
        db.add(match)

        review_row = Review(
            id=str(generate_uuidv7()),
            match_id=match_id,
            status="APPROVED",
            decision="MODIFY",
            reviewer_id=user_id,
            ai_relationship=match.relationship,
            human_relationship="FUNCTIONALLY_EQUIVALENT",
            reason_code="REMAPPED_TO_EXISTING_NMC",
            comment=reason,
            evidence_snapshot={"remapped_nmc": nat_mat.nmc}
        )
        db.add(review_row)
        db.commit()

        AuditService.record(
            db=db,
            actor_role="DATA_STEWARD",
            action="MATERIAL_REMAPPED",
            entity_type="material_match",
            entity_id=match_id,
            actor_id=user_id,
            before={"review_status": old_status, "previous_national_uid": existing_leg.national_material_uid if existing_leg else None},
            after={"target_nmc": nat_mat.nmc, "target_uid": nat_mat.uid},
            reason=f"Remapped material {mat_a.source_code} to NMC {nat_mat.nmc}. Reason: {reason or 'Steward modification'}"
        )

        return review_row, leg_row
