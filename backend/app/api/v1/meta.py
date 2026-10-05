from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import ModelVersion
from app.core.config import settings

router = APIRouter(prefix="/meta", tags=["Metadata"])

@router.get("/version")
def get_meta_version(db: Session = Depends(get_db)):
    active_models = db.query(ModelVersion).filter_by(status="ACTIVE").all()
    models_summary = [
        {
            "id": m.id,
            "kind": m.kind,
            "provider": m.provider,
            "model_id": m.model_id,
            "model_version": m.model_version,
            "config_hash": m.config_hash
        }
        for m in active_models
    ]
    
    return {
        "app_name": settings.APP_NAME,
        "app_version": "2.11.0",
        "env": settings.ENV,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_badge": f"LLM: {settings.LLM_PROVIDER.upper()}",
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "embedding_model": settings.EMBEDDING_MODEL,
        "active_model_versions": models_summary
    }

@router.get("/demo-scenarios")
def get_demo_scenarios(db: Session = Depends(get_db)):
    """
    Returns verified curated demo scenario targets for judges to walk through the golden path.
    All targets reference real database entities evaluated by the engine.
    """
    from app.db.models import MaterialMatch, Material, NationalMaterial, LegacyMapping

    # 1. 8.8 vs 10.9 Trap Match
    trap_88_109 = None
    for m in db.query(MaterialMatch).filter_by(relationship="NOT_EQUIVALENT").limit(100).all():
        if m.veto and m.veto.get("applied") and ("8.8" in str(m.veto) and "10.9" in str(m.veto)):
            trap_88_109 = {
                "match_id": m.id,
                "relationship": m.relationship,
                "confidence": m.equivalence_confidence,
                "gate": m.veto.get("gate_id", "G2"),
                "reason": m.veto.get("reason", "Property class conflict (8.8 vs 10.9)")
            }
            break

    # Fallback to any G2 veto if specific pair not found
    if not trap_88_109:
        for m in db.query(MaterialMatch).filter_by(relationship="NOT_EQUIVALENT").limit(100).all():
            if m.veto and m.veto.get("gate_id") == "G2":
                trap_88_109 = {
                    "match_id": m.id,
                    "relationship": m.relationship,
                    "confidence": m.equivalence_confidence,
                    "gate": "G2",
                    "reason": m.veto.get("reason", "Critical attribute conflict")
                }
                break

    # 2. Unknown / Missing Grade Gate (G4 or REVIEW_REQUIRED)
    trap_unknown = None
    for m in db.query(MaterialMatch).filter_by(relationship="REVIEW_REQUIRED").limit(100).all():
        trap_unknown = {
            "match_id": m.id,
            "relationship": m.relationship,
            "confidence": m.equivalence_confidence,
            "gate": m.veto.get("gate_id") if m.veto else "G4",
            "reason": m.explanation or "Missing critical specification requires human steward review"
        }
        break

    # 3. Safe Equivalent Pair (ready for review / approved)
    safe_equiv = None
    for m in db.query(MaterialMatch).filter_by(relationship="FUNCTIONALLY_EQUIVALENT").order_by(MaterialMatch.equivalence_confidence.desc()).limit(100).all():
        safe_equiv = {
            "match_id": m.id,
            "relationship": m.relationship,
            "confidence": m.equivalence_confidence,
            "review_status": m.review_status
        }
        break

    # 4. Active National Material
    nat_mat = db.query(NationalMaterial).filter_by(status="ACTIVE").first()

    return {
        "is_demo_ready": True,
        "scenarios": {
            "trap_88_109": trap_88_109,
            "trap_unknown": trap_unknown,
            "safe_equivalent": safe_equiv,
            "national_material": {
                "uid": nat_mat.uid if nat_mat else None,
                "nmc": nat_mat.nmc if nat_mat else None,
                "description": nat_mat.canonical_description if nat_mat else None
            } if nat_mat else None
        }
    }


@router.get("/public-stats")
def get_public_stats(db: Session = Depends(get_db)):
    """
    Public aggregate counts for the landing page without requiring authentication.
    Reflects the actual PostgreSQL database contents including real public datasets.
    """
    from app.db.models import Material, MaterialMatch, Cpse, Classification, NationalMaterial

    total_materials = db.query(Material).count()
    real_public_count = db.query(Material).filter(Material.provenance == "REAL_PUBLIC").count()
    demo_count = db.query(Material).filter(Material.provenance == "CONTROLLED_GOLDEN_DEMO").count()
    cpse_count = db.query(Cpse).count()
    category_count = db.query(Classification.category_code).distinct().count()
    
    safe_equiv = db.query(MaterialMatch).filter(
        MaterialMatch.relationship.in_(["FUNCTIONALLY_EQUIVALENT", "NEAR_DUPLICATE", "EXACT_DUPLICATE"])
    ).count()
    
    vetoed_count = db.query(MaterialMatch).filter(
        MaterialMatch.relationship == "NOT_EQUIVALENT"
    ).count()
    
    national_materials = db.query(NationalMaterial).count()

    return {
        "total_materials": total_materials,
        "real_public_materials": real_public_count,
        "controlled_demo_materials": demo_count,
        "cpses": cpse_count,
        "categories": category_count,
        "safe_equiv": safe_equiv,
        "vetoed_count": vetoed_count,
        "national_materials": national_materials,
        "gates": "G0–G6"
    }

@router.get("/model-assurance")
def get_model_assurance(db: Session = Depends(get_db)):
    """
    Model Assurance & Governance telemetry endpoint.
    Exposes measured benchmark evidence from reports/model_benchmark_latest.json
    and real database model registrations. Strictly labeled CONTROLLED BENCHMARK.
    """
    import json
    from pathlib import Path

    benchmark_path = Path("reports/model_benchmark_latest.json")
    benchmark_data = None
    if benchmark_path.exists():
        try:
            with open(benchmark_path, "r", encoding="utf-8") as f:
                benchmark_data = json.load(f)
        except Exception:
            pass

    active_models = db.query(ModelVersion).all()
    models_list = [
        {
            "id": m.id,
            "kind": m.kind,
            "provider": m.provider,
            "model_id": m.model_id,
            "model_version": m.model_version,
            "dimension": m.dimension,
            "status": m.status
        }
        for m in active_models
    ]

    return {
        "status": "ASSURED",
        "benchmark_label": "CONTROLLED BENCHMARK — NOT PRODUCTION ACCURACY",
        "active_embedding_provider": settings.EMBEDDING_PROVIDER,
        "active_embedding_model": settings.EMBEDDING_MODEL,
        "active_reranker_provider": settings.RERANKER_PROVIDER,
        "active_llm_provider": settings.LLM_PROVIDER,
        "registered_models": models_list,
        "latest_benchmark": benchmark_data
    }


