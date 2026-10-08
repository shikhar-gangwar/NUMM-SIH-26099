import os
import json
import logging
import datetime
import numpy as np
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

CACHE_DIR = os.getenv("NLP_CACHE_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "cache"))

class EmbeddingCache:
    """
    Disk-backed and in-memory embedding cache keyed by SHA-256 text_hash.
    Avoids recomputing sentence-transformers embeddings for unchanged material texts.
    """

    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = os.path.abspath(cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)
        self.memory_cache: Dict[str, Dict[str, Any]] = {}

    def _get_paths(self, text_hash: str):
        vec_path = os.path.join(self.cache_dir, f"{text_hash}.npy")
        meta_path = os.path.join(self.cache_dir, f"{text_hash}.json")
        return vec_path, meta_path

    def get(self, text_hash: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves cached embedding entry by text_hash if present.
        """
        if text_hash in self.memory_cache:
            return self.memory_cache[text_hash]

        vec_path, meta_path = self._get_paths(text_hash)
        if os.path.exists(vec_path) and os.path.exists(meta_path):
            try:
                embedding = np.load(vec_path)
                with open(meta_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                entry = {
                    "material_id": metadata.get("material_id"),
                    "normalized_text": metadata.get("normalized_text"),
                    "text_hash": text_hash,
                    "embedding": embedding,
                    "embedding_model": metadata.get("embedding_model"),
                    "embedding_created_at": metadata.get("embedding_created_at")
                }
                self.memory_cache[text_hash] = entry
                return entry
            except Exception as e:
                logger.warning(f"Error reading embedding cache for {text_hash}: {e}")

        return None

    def put(self, text_hash: str, normalized_text: str, embedding: np.ndarray, material_id: Optional[str] = None, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> Dict[str, Any]:
        """
        Saves an embedding entry to disk and in-memory cache.
        """
        vec_path, meta_path = self._get_paths(text_hash)
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        metadata = {
            "material_id": material_id,
            "normalized_text": normalized_text,
            "text_hash": text_hash,
            "embedding_model": model_name,
            "embedding_created_at": created_at
        }

        try:
            np.save(vec_path, embedding.astype(np.float32))
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            logger.warning(f"Error writing embedding cache for {text_hash}: {e}")

        entry = {
            "material_id": material_id,
            "normalized_text": normalized_text,
            "text_hash": text_hash,
            "embedding": embedding.astype(np.float32),
            "embedding_model": model_name,
            "embedding_created_at": created_at
        }
        self.memory_cache[text_hash] = entry
        return entry

# Global singleton instance
embedding_cache = EmbeddingCache()
