from typing import List
import hashlib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
import numpy as np
from app.ai.providers.base import EmbeddingProvider, ModelFingerprint

class TfidfEmbedding(EmbeddingProvider):
    def __init__(self, dimension: int = 384):
        self.name = "tfidf"
        self.model_id = "char-ngram-tfidf-svd"
        self.version = "v1"
        self.dimension = dimension
        self.vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(3, 5))
        self.svd = TruncatedSVD(n_components=dimension, random_state=42)
        self.is_fitted = False

    def fit(self, texts: List[str]):
        if len(texts) > 0:
            matrix = self.vectorizer.fit_transform(texts)
            n_components = min(self.dimension, matrix.shape[1] - 1 if matrix.shape[1] > 1 else 1)
            self.svd = TruncatedSVD(n_components=n_components, random_state=42)
            self.svd.fit(matrix)
            self.is_fitted = True

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not self.is_fitted:
            self.fit(texts if len(texts) > 1 else texts + ["placeholder text"])
        
        matrix = self.vectorizer.transform(texts)
        if matrix.shape[1] == 0:
            return [[0.0] * self.dimension for _ in texts]
        
        vecs = self.svd.transform(matrix)
        # Pad if dimension < expected
        if vecs.shape[1] < self.dimension:
            pad_width = self.dimension - vecs.shape[1]
            vecs = np.pad(vecs, ((0, 0), (0, pad_width)))
        
        # Normalize
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        vecs = vecs / norms
        return vecs.tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]

    def fingerprint(self) -> ModelFingerprint:
        return ModelFingerprint(
            provider=self.name,
            model_id=self.model_id,
            model_version=self.version,
            dimension=self.dimension
        )
