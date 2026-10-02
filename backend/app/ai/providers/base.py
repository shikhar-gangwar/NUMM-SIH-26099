from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class ModelFingerprint:
    def __init__(self, provider: str, model_id: str, model_version: str, revision_or_digest: str = "", dimension: Optional[int] = None, params_hash: str = ""):
        self.provider = provider
        self.model_id = model_id
        self.model_version = model_version
        self.revision_or_digest = revision_or_digest
        self.dimension = dimension
        self.params_hash = params_hash

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "revision_or_digest": self.revision_or_digest,
            "dimension": self.dimension,
            "params_hash": self.params_hash
        }

class EmbeddingProvider(ABC):
    name: str
    version: str
    dimension: int

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        pass

    @abstractmethod
    def fingerprint(self) -> ModelFingerprint:
        pass

class RerankerProvider(ABC):
    name: str
    version: str

    @abstractmethod
    def score_pairs(self, pairs: List[tuple[str, str]]) -> List[float]:
        pass

    @abstractmethod
    def fingerprint(self) -> ModelFingerprint:
        pass

class LLMProvider(ABC):
    name: str
    version: str

    @abstractmethod
    def complete_json(self, task: str, payload: dict, schema: dict, temperature: float = 0.0) -> dict:
        pass

    @abstractmethod
    def fingerprint(self) -> ModelFingerprint:
        pass
