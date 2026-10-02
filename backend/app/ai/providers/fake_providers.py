import hashlib
from typing import List
from app.ai.providers.base import EmbeddingProvider, LLMProvider, ModelFingerprint

class FakeEmbedding(EmbeddingProvider):
    def __init__(self, dimension: int = 384):
        self.name = "fake"
        self.model_id = "fake-hash-embedding"
        self.version = "v1"
        self.dimension = dimension

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        results = []
        for text in texts:
            # Deterministic hash-based vector
            seed = hashlib.md5(text.encode("utf-8")).digest()
            vec = []
            for i in range(self.dimension):
                val = (seed[i % len(seed)] / 255.0) * 2.0 - 1.0
                vec.append(val)
            # Normalize vector
            norm = sum(x*x for x in vec) ** 0.5
            norm = norm if norm > 0 else 1.0
            vec = [x / norm for x in vec]
            results.append(vec)
        return results

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]

    def fingerprint(self) -> ModelFingerprint:
        return ModelFingerprint(
            provider=self.name,
            model_id=self.model_id,
            model_version=self.version,
            dimension=self.dimension
        )

class FakeLLM(LLMProvider):
    def __init__(self):
        self.name = "fake"
        self.model_id = "fake-canned-llm"
        self.version = "v1"

    def complete_json(self, task: str, payload: dict, schema: dict, temperature: float = 0.0) -> dict:
        return {"extracted_attributes": {}, "explanation": "Fake LLM canned explanation"}

    def fingerprint(self) -> ModelFingerprint:
        return ModelFingerprint(
            provider=self.name,
            model_id=self.model_id,
            model_version=self.version
        )
