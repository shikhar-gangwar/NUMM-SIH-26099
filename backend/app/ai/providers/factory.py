from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.models import ModelVersion
from app.ai.providers.base import EmbeddingProvider, LLMProvider
from app.ai.providers.sentence_transformers import SentenceTransformersEmbedding
from app.ai.providers.tfidf import TfidfEmbedding
from app.ai.providers.none_llm import NoneLLM
from app.ai.providers.fake_providers import FakeEmbedding, FakeLLM

def register_provider_fingerprint(db: Session | None, provider_inst) -> ModelVersion | None:
    if db is None:
        return None
    fp = provider_inst.fingerprint()
    existing = db.query(ModelVersion).filter_by(
        provider=fp.provider,
        model_id=fp.model_id,
        model_version=fp.model_version
    ).first()
    if existing:
        return existing
    
    mv = ModelVersion(
        kind="EMBEDDING" if isinstance(provider_inst, EmbeddingProvider) else "LLM",
        provider=fp.provider,
        model_id=fp.model_id,
        model_version=fp.model_version,
        dimension=fp.dimension,
        status="ACTIVE"
    )
    db.add(mv)
    db.commit()
    db.refresh(mv)
    return mv

def get_embedding_provider(db: Session | None = None) -> EmbeddingProvider:
    provider_name = settings.EMBEDDING_PROVIDER.lower()
    if provider_name == "sentence_transformers":
        try:
            inst = SentenceTransformersEmbedding(settings.EMBEDDING_MODEL, settings.EMBEDDING_DEVICE)
        except Exception:
            # Fallback to TF-IDF if model fails to load
            inst = TfidfEmbedding(settings.EMBEDDING_DIM)
    elif provider_name == "tfidf":
        inst = TfidfEmbedding(settings.EMBEDDING_DIM)
    elif provider_name == "fake":
        inst = FakeEmbedding(settings.EMBEDDING_DIM)
    else:
        raise ValueError(f"Unknown EMBEDDING_PROVIDER: {settings.EMBEDDING_PROVIDER}")
    
    if db:
        register_provider_fingerprint(db, inst)
    return inst

def get_llm_provider(db: Session | None = None) -> LLMProvider:
    provider_name = settings.LLM_PROVIDER.lower()
    if provider_name == "none":
        inst = NoneLLM()
    elif provider_name == "fake":
        inst = FakeLLM()
    else:
        inst = NoneLLM()
    
    if db:
        register_provider_fingerprint(db, inst)
    return inst
