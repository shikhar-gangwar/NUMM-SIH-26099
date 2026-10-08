from typing import List
import numpy as np
from app.ai.providers.base import EmbeddingProvider, ModelFingerprint

class SentenceTransformersEmbedding(EmbeddingProvider):
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", device: str = "cpu"):
        self.name = "sentence-transformers"
        self.model_id = model_name
        self.version = "v2"
        self.dimension = 384
        self.device = device
        self._model = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_id, device=self.device)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        self._load_model()
        embeddings = self._model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]

    def fingerprint(self) -> ModelFingerprint:
        return ModelFingerprint(
            provider=self.name,
            model_id=self.model_id,
            model_version=self.version,
            dimension=self.dimension
        )
