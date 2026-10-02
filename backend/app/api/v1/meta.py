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
        "app_version": "0.1.0",
        "env": settings.ENV,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_badge": f"LLM: {settings.LLM_PROVIDER.upper()}",
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "embedding_model": settings.EMBEDDING_MODEL,
        "active_model_versions": models_summary
    }
