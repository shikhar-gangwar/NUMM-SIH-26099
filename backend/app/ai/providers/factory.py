from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.models import ModelVersion
from app.ai.providers.base import EmbeddingProvider, RerankerProvider, LLMProvider
from app.ai.providers.sentence_transformers import SentenceTransformersEmbedding
from app.ai.providers.tfidf import TfidfEmbedding
from app.ai.providers.none_llm import NoneLLM
from app.ai.providers.fake_providers import FakeEmbedding, FakeLLM
from app.ai.providers.qwen import Qwen3EmbeddingProvider, Qwen3RerankerProvider

def register_provider_fingerprint(db: Session | None, provider_inst) -> ModelVersion | None:
    if db is None or provider_inst is None:
        return None
    fp = provider_inst.fingerprint()
    existing = db.query(ModelVersion).filter_by(
        provider=fp.provider,
        model_id=fp.model_id,
        model_version=fp.model_version
    ).first()
    if existing:
        return existing
    
    if isinstance(provider_inst, EmbeddingProvider):
        kind = "EMBEDDING"
    elif isinstance(provider_inst, RerankerProvider):
        kind = "RERANKER"
    else:
        kind = "LLM"

    mv = ModelVersion(
        kind=kind,
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

_cached_embedding_provider: EmbeddingProvider | None = None

def get_embedding_provider(db: Session | None = None, provider_override: str | None = None) -> EmbeddingProvider:
    global _cached_embedding_provider
    if provider_override is None and _cached_embedding_provider is not None:
        if db:
            register_provider_fingerprint(db, _cached_embedding_provider)
        return _cached_embedding_provider

    provider_name = (provider_override or settings.EMBEDDING_PROVIDER).lower()
    if provider_name == "sentence_transformers":
        try:
            inst = SentenceTransformersEmbedding(settings.EMBEDDING_MODEL, settings.EMBEDDING_DEVICE)
            inst._load_model()
        except Exception:
            # Fallback to TF-IDF if model fails to load
            inst = TfidfEmbedding(settings.EMBEDDING_DIM)
    elif provider_name in ["qwen3_0_6b", "qwen", "qwen3"]:
        inst = Qwen3EmbeddingProvider(
            model_name=settings.QWEN_EMBEDDING_MODEL,
            dimension=settings.QWEN_EMBEDDING_DIM,
            device=settings.EMBEDDING_DEVICE
        )
    elif provider_name == "tfidf":
        inst = TfidfEmbedding(settings.EMBEDDING_DIM)
    elif provider_name == "fake":
        inst = FakeEmbedding(settings.EMBEDDING_DIM)
    else:
        raise ValueError(f"Unknown EMBEDDING_PROVIDER: {provider_name}")
    
    if db:
        register_provider_fingerprint(db, inst)
    if provider_override is None:
        _cached_embedding_provider = inst
    return inst

_cached_reranker_provider: RerankerProvider | None = None

def get_reranker_provider(db: Session | None = None, provider_override: str | None = None) -> RerankerProvider | None:
    global _cached_reranker_provider
    if provider_override is None and _cached_reranker_provider is not None:
        if db:
            register_provider_fingerprint(db, _cached_reranker_provider)
        return _cached_reranker_provider

    provider_name = (provider_override or settings.RERANKER_PROVIDER).lower()
    if provider_name in ["none", "", "off"]:
        return None
    elif provider_name in ["qwen3_0_6b", "qwen", "qwen3", "qwen_reranker"]:
        inst = Qwen3RerankerProvider(
            model_name=settings.QWEN_RERANKER_MODEL,
            device=settings.EMBEDDING_DEVICE
        )
    else:
        return None

    if db:
        register_provider_fingerprint(db, inst)
    if provider_override is None:
        _cached_reranker_provider = inst
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
