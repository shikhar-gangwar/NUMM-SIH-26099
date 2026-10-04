import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.db.models import NationalMaterial, LegacyMapping, Material, Cpse, IntegrationJob, SapMockMaterial
from app.audit.service import AuditService
from app.core.ids import generate_uuidv7

class MockSapAdapter:
    """
    Mock SAP S/4HANA / ECC Master Data Integration Adapter.
    
    IMPORTANT: This adapter explicitly produces mock/prototype ERP synchronization payloads.
    It simulates an SAP BAPI_MATERIAL_SAVEDATA / IDoc MATMAS outbound interface.
    Strictly enforces SAP 40-character short description limit (MAKT-MAKTX).
    """

    ADAPTER_NAME = "MOCK_SAP_S4HANA"
    SAP_SYSTEM_ID = "S4H_PRD_MOCK"
    SAP_CLIENT = "100"
    MAX_DESCRIPTION_LEN = 40

    @classmethod
    def truncate_description(cls, raw_desc: str) -> str:
        """
        Enforces standard SAP 40-character MAKT-MAKTX constraint.
        """
        if not raw_desc:
            return "UNNAMED MATERIAL"
        clean = " ".join(raw_desc.strip().split())
        if len(clean) <= cls.MAX_DESCRIPTION_LEN:
            return clean
        # Truncate at 40 chars
        return clean[:cls.MAX_DESCRIPTION_LEN]

    @classmethod
    def derive_sap_matnr(cls, nat_mat: NationalMaterial) -> str:
        """
        Generates SAP MATNR standard number from NMC.
        Example: NMC-BOLT-00000042-X -> MAT-BOLT-00000042
        """
        parts = nat_mat.nmc.split("-")
        if len(parts) >= 4:
            cat = parts[1]
            seq = parts[2]
            return f"MAT-{cat[:4]}-{seq[:8]}"
        clean_nmc = nat_mat.nmc.replace("NMC-", "")[:35]
        return f"MAT-{clean_nmc}"

    @classmethod
    def sync_national_materials(
        cls,
        db: Session,
        actor_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes an outbound synchronization of all approved National Materials
        to the simulated SAP S/4HANA material master table.
        """
        # 1. Fetch all active National Materials
        national_materials = db.query(NationalMaterial).filter_by(status="ACTIVE").all()

        sync_job_id = str(generate_uuidv7())
        exported_records: List[Dict[str, Any]] = []
        category_counts: Dict[str, int] = {}

        for nm in national_materials:
            sap_matnr = cls.derive_sap_matnr(nm)
            maktx = cls.truncate_description(nm.canonical_description)

            # Count mapped CPSE materials
            mappings = db.query(LegacyMapping).filter_by(
                national_material_uid=nm.uid,
                status="ACTIVE"
            ).all()

            mapped_cpse_codes = []
            for m in mappings:
                mat = db.query(Material).filter_by(id=m.material_id).first()
                if mat:
                    cpse = db.query(Cpse).filter_by(id=mat.cpse_id).first()
                    if cpse and cpse.code not in mapped_cpse_codes:
                        mapped_cpse_codes.append(cpse.code)

            # BAPI payload structure
            payload = {
                "HEADER": {
                    "SAP_SYSTEM_ID": cls.SAP_SYSTEM_ID,
                    "SAP_CLIENT": cls.SAP_CLIENT,
                    "MATNR": sap_matnr,
                    "MTART": "ROH", # Raw Material / Spare
                    "MATKL": nm.category_code,
                    "MEINS": "EA",
                    "SPRAS": "EN"
                },
                "MAKT": {
                    "MAKTX": maktx,
                    "CHAR_LIMIT_ENFORCED": cls.MAX_DESCRIPTION_LEN,
                    "ORIGINAL_LEN": len(nm.canonical_description),
                    "WAS_TRUNCATED": len(nm.canonical_description) > cls.MAX_DESCRIPTION_LEN
                },
                "NUMM_CROSSWALK": {
                    "NMC": nm.nmc,
                    "NATIONAL_UID": nm.uid,
                    "SPEC_FINGERPRINT": nm.spec_fingerprint,
                    "MAPPED_CPSE_COUNT": len(mapped_cpse_codes),
                    "MAPPED_CPSES": mapped_cpse_codes
                },
                "IS_MOCK": True,
                "SYNCED_AT": datetime.now(timezone.utc).isoformat()
            }


            # Upsert into SapMockMaterial table (match on sap_product_id or nmc)
            sap_row = db.query(SapMockMaterial).filter(
                (SapMockMaterial.sap_product_id == sap_matnr) | (SapMockMaterial.nmc == nm.nmc)
            ).first()
            if not sap_row:
                sap_row = SapMockMaterial(
                    id=str(generate_uuidv7()),
                    sap_product_id=sap_matnr,
                    product_description=maktx,
                    nmc=nm.nmc,
                    payload=payload,
                    status="SYNCED",
                    created_at=datetime.now(timezone.utc)
                )
                db.add(sap_row)
            else:
                sap_row.sap_product_id = sap_matnr
                sap_row.nmc = nm.nmc
                sap_row.product_description = maktx
                sap_row.payload = payload
                sap_row.status = "SYNCED"
                db.add(sap_row)

            exported_records.append({
                "sap_product_id": sap_matnr,
                "nmc": nm.nmc,
                "maktx": maktx,
                "category": nm.category_code,
                "cpse_count": len(mapped_cpse_codes)
            })

            category_counts[nm.category_code] = category_counts.get(nm.category_code, 0) + 1

        db.commit()

        # 2. Record IntegrationJob
        counts = {
            "exported": len(exported_records),
            "accepted": len(exported_records),
            "rejected": 0,
            "categories": category_counts
        }

        job = IntegrationJob(
            id=sync_job_id,
            adapter=cls.ADAPTER_NAME,
            direction="OUTBOUND_SYNC",
            payload_ref=f"s4h_sync_{sync_job_id[:8]}",
            status="COMPLETED",
            counts=counts,
            is_mock=True,
            created_at=datetime.now(timezone.utc)
        )
        db.add(job)
        db.commit()

        # 3. Append to Audit Hash Chain
        AuditService.record(
            db=db,
            actor_role="DATA_STEWARD",
            action="MOCK_SAP_SYNC_COMPLETED",
            entity_type="integration_job",
            entity_id=sync_job_id,
            actor_id=actor_id,
            after=counts,
            reason=f"Synchronized {len(exported_records)} National Materials to Mock SAP ERP adapter."
        )

        return {
            "sync_id": sync_job_id,
            "status": "COMPLETED",
            "is_mock": True,
            "adapter": cls.ADAPTER_NAME,
            "system_id": cls.SAP_SYSTEM_ID,
            "client": cls.SAP_CLIENT,
            "records_exported": len(exported_records),
            "records_accepted": len(exported_records),
            "records_rejected": 0,
            "timestamp": job.created_at.isoformat(),
            "details": exported_records
        }

    @classmethod
    def get_status(cls, db: Session) -> Dict[str, Any]:
        """
        Returns status summary of the mock SAP integration.
        """
        latest_job = db.query(IntegrationJob).filter_by(
            adapter=cls.ADAPTER_NAME
        ).order_by(IntegrationJob.created_at.desc()).first()

        total_synced_materials = db.query(SapMockMaterial).count()

        return {
            "adapter": cls.ADAPTER_NAME,
            "is_mock": True,
            "status": "READY" if not latest_job else latest_job.status,
            "system_id": cls.SAP_SYSTEM_ID,
            "client": cls.SAP_CLIENT,
            "description_limit": cls.MAX_DESCRIPTION_LEN,
            "total_synced_materials": total_synced_materials,
            "last_sync": {
                "sync_id": latest_job.id if latest_job else None,
                "status": latest_job.status if latest_job else None,
                "timestamp": latest_job.created_at.isoformat() if latest_job else None,
                "records_exported": latest_job.counts.get("exported", 0) if latest_job and latest_job.counts else 0,
                "records_accepted": latest_job.counts.get("accepted", 0) if latest_job and latest_job.counts else 0,
                "records_rejected": latest_job.counts.get("rejected", 0) if latest_job and latest_job.counts else 0,
            } if latest_job else None
        }

    @classmethod
    def list_synced_materials(
        cls,
        db: Session,
        page: int = 1,
        page_size: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Returns paginated records from the mock SAP material master.
        """
        offset = (page - 1) * page_size
        rows = db.query(SapMockMaterial).order_by(
            SapMockMaterial.created_at.desc()
        ).offset(offset).limit(page_size).all()

        return [
            {
                "id": r.id,
                "sap_product_id": r.sap_product_id,
                "product_description": r.product_description,
                "nmc": r.nmc,
                "status": r.status,
                "payload": r.payload,
                "created_at": r.created_at.isoformat() if r.created_at else None
            } for r in rows
        ]

class SAPS4Adapter:
    """
    Production SAP S/4HANA OData / RFC Outbound Material Master Interface Contract.
    Conforms to SAP Material Master API (API_PRODUCT_SRV / ProductMaster).
    
    SECURITY INVARIANT (Rule 17):
    Real RFC/OData credentials remain external in environment secrets (e.g. SAP_HOST, SAP_API_KEY).
    No credentials are ever committed or mocked with fake production status.
    """
    ADAPTER_NAME = "SAP_S4HANA_ODATA_V2"
    SAP_MAX_MAKTX_LEN = 40

    def __init__(
        self,
        base_url: Optional[str] = None,
        client: str = "100",
        auth_type: str = "OAUTH2"
    ):
        self.base_url = base_url
        self.client = client
        self.auth_type = auth_type

    def transform_nmc_to_product_payload(
        self,
        nmc: str,
        canonical_desc: str,
        uom: str,
        category: str
    ) -> Dict[str, Any]:
        """
        Transforms NUMM canonical master data into SAP S/4HANA Product Master JSON schema.
        Enforces 40-character MAKTX truncation.
        """
        short_desc = canonical_desc[:self.SAP_MAX_MAKTX_LEN] if len(canonical_desc) > self.SAP_MAX_MAKTX_LEN else canonical_desc
        return {
            "Product": nmc.replace("-", "")[:18],
            "ProductType": "ROH" if category in ["PIPE", "BOLT"] else "ERSA",
            "BaseUnit": uom if uom else "EA",
            "to_Description": [
                {
                    "Language": "EN",
                    "ProductDescription": short_desc
                }
            ],
            "ProductGroup": category,
            "IndustrySector": "M"  # Mechanical Engineering
        }

    def health_check(self) -> Dict[str, Any]:
        return {
            "adapter": self.ADAPTER_NAME,
            "is_mock": False,
            "configured": bool(self.base_url),
            "auth_type": self.auth_type,
            "status": "UNCONFIGURED_CREDENTIALS_REQUIRED" if not self.base_url else "CONFIGURED"
        }

