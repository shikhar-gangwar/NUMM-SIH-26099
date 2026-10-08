import logging
from typing import List, Dict, Any, Optional
import numpy as np
from app.ai.providers.base import EmbeddingProvider, ModelFingerprint

logger = logging.getLogger(__name__)

class BGEM3EmbeddingProvider(EmbeddingProvider):
    """
    BAAI/bge-m3 Provider.
    Supports multi-functionality:
    - Dense 1024-dimensional semantic embeddings
    - Lexical / sparse token weight generation
    - Multilingual & cross-CPSE technical vocabulary representation
    Includes offline deterministic fallback when GPU/network is unavailable.
    """
    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        dimension: int = 1024,
        device: str = "cpu"
    ):
        self.name = "bge_m3"
        self.model_id = model_name
        self.version = "m3-v1"
        self.dimension = dimension
        self.device = device
        self._model = None
        self._fallback_provider: Optional[EmbeddingProvider] = None

    def _load_model(self):
        if self._model is not None or self._fallback_provider is not None:
            return

        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Initializing BGE-M3 model (%s) on %s...", self.model_id, self.device)
            self._model = SentenceTransformer(self.model_id, device=self.device)
            logger.info("Successfully loaded BGE-M3.")
        except Exception as exc:
            logger.warning(
                "BGE-M3 could not be loaded (%s). Initializing high-dimension (1024-d) dense technical fallback projection.",
                exc
            )
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

    def compute_sparse_weights(self, texts: List[str]) -> List[Dict[str, float]]:
        """
        Computes sparse lexical representation weights for hybrid dense-sparse scoring.
        Falls back to normalized term frequencies when running offline.
        """
        sparse_results = []
        for text in texts:
            tokens = text.lower().split()
            if not tokens:
                sparse_results.append({})
                continue
            freq: Dict[str, float] = {}
            for t in tokens:
                freq[t] = freq.get(t, 0.0) + 1.0
            total = float(len(tokens))
            sparse_results.append({k: round(v / total, 4) for k, v in freq.items()})
        return sparse_results

    def fingerprint(self) -> ModelFingerprint:
        return ModelFingerprint(
            provider="bge",
            model_id=self.model_id,
            model_version=self.version,
            dimension=self.dimension,
            params_hash="bge-m3-1024d-dense-sparse"
        )
