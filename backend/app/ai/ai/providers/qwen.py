import logging
from typing import List, Optional
import numpy as np
from app.ai.providers.base import EmbeddingProvider, RerankerProvider, ModelFingerprint

logger = logging.getLogger(__name__)

class Qwen3EmbeddingProvider(EmbeddingProvider):
    """
    Qwen3-Embedding-0.6B Provider (1024-dimensional dense vectors).
    Provides high-resolution semantic representation for industrial technical descriptions.
    Includes deterministic fallback when running in offline or resource-constrained CPU environments.
    """
    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-Embedding-0.6B",
        dimension: int = 1024,
        device: str = "cpu"
    ):
        self.name = "qwen"
        self.model_id = model_name
        self.version = "0.6b-v1"
        self.dimension = dimension
        self.device = device
        self._model = None
        self._fallback_provider: Optional[EmbeddingProvider] = None

    def _load_model(self):
        if self._model is not None or self._fallback_provider is not None:
            return

        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Initializing Qwen3-Embedding-0.6B model (%s) on %s...", self.model_id, self.device)
            self._model = SentenceTransformer(self.model_id, device=self.device)
            logger.info("Successfully loaded Qwen3-Embedding-0.6B.")
        except Exception as exc:
            logger.warning(
                "Qwen3-Embedding-0.6B could not be initialized directly (%s). Initializing high-dimension (1024-d) dense technical fallback projection.",
                exc
            )
            # Use deterministic 1024-dimensional SVD/TF-IDF projection to guarantee uninterrupted operation
            from app.ai.providers.tfidf import TfidfEmbedding
            self._fallback_provider = TfidfEmbedding(dimension=self.dimension)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        self._load_model()
        if self._model is not None:
            embeddings = self._model.encode(texts, normalize_embeddings=True)
            return embeddings.tolist()
        elif self._fallback_provider is not None:
            return self._fallback_provider.embed_documents(texts)
        else:
            return [[0.0] * self.dimension for _ in texts]

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]

    def fingerprint(self) -> ModelFingerprint:
        return ModelFingerprint(
            provider=self.name,
            model_id=self.model_id,
            model_version=self.version,
            dimension=self.dimension,
            params_hash="qwen3-0.6b-dense"
        )


class Qwen3RerankerProvider(RerankerProvider):
    """
    Qwen3-Reranker-0.6B Cross-Encoder Provider.
    Scores (query, candidate) text pairs for contextual precision ranking.
    Safety Note: Output scores are strictly candidate-ordering signals and NEVER bypass G0-G6 veto gates.
    """
    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-Reranker-0.6B",
        device: str = "cpu"
    ):
        self.name = "qwen-reranker"
        self.model_id = model_name
        self.version = "0.6b-v1"
        self.device = device
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return
        try:
            from sentence_transformers import CrossEncoder
            logger.info("Initializing Qwen3-Reranker-0.6B model (%s) on %s...", self.model_id, self.device)
            self._model = CrossEncoder(self.model_id, device=self.device)
            logger.info("Successfully loaded Qwen3-Reranker-0.6B.")
        except Exception as exc:
            logger.warning("Qwen3-Reranker-0.6B offline or unavailable: %s. Using lexical-overlap scoring fallback.", exc)
            self._model = "FALLBACK"

    def score_pairs(self, pairs: List[tuple[str, str]]) -> List[float]:
        self._load_model()
        if self._model is not None and self._model != "FALLBACK":
            import torch
            with torch.no_grad():
                scores = self._model.predict(pairs)
                # Apply sigmoid if logits
                if hasattr(scores, "tolist"):
                    return [float(1.0 / (1.0 + np.exp(-s))) for s in scores.tolist()]
                return [float(1.0 / (1.0 + np.exp(-s))) for s in scores]
        
        # Deterministic token set similarity fallback
        from rapidfuzz import fuzz
        fallback_scores = []
        for q, c in pairs:
            sim = fuzz.token_set_ratio(q.upper(), c.upper()) / 100.0
            fallback_scores.append(float(sim))
        return fallback_scores

    def fingerprint(self) -> ModelFingerprint:
        return ModelFingerprint(
            provider=self.name,
            model_id=self.model_id,
            model_version=self.version,
            dimension=None,
            params_hash="qwen3-0.6b-cross-encoder"
        )
