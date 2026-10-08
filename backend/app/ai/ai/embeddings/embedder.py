import os
import logging
import torch
import numpy as np
from typing import List, Union
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_BATCH_SIZE = 16
DEFAULT_CPU_THREADS = 2

class CPUMaterialEmbedder:
    """
    CPU-optimized embedder singleton using sentence-transformers/all-MiniLM-L6-v2.
    Enforces thread limits, torch.inference_mode(), and batching for low CPU/RAM overhead.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(CPUMaterialEmbedder, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, cpu_threads: int = DEFAULT_CPU_THREADS):
        if self._initialized:
            return

        # Restrict PyTorch CPU thread count to prevent laptop overheating
        try:
            torch.set_num_threads(cpu_threads)
            torch.set_num_interop_threads(cpu_threads)
        except Exception as e:
            logger.warning(f"Could not set PyTorch thread limits: {e}")

        logger.info(f"Loading {MODEL_NAME} on CPU (threads={cpu_threads})...")
        self.device = "cpu"
        self.model = SentenceTransformer(MODEL_NAME, device=self.device)
        self.embedding_dimension = self.model.get_sentence_embedding_dimension() # 384
        self._initialized = True
        logger.info(f"Model {MODEL_NAME} loaded successfully. Dimension: {self.embedding_dimension}")

    def embed_single(self, text: str) -> np.ndarray:
        """
        Embeds a single normalized text string.
        Returns a 1D numpy float32 array of shape (384,).
        """
        if not text:
            return np.zeros((self.embedding_dimension,), dtype=np.float32)

        with torch.inference_mode():
            embedding = self.model.encode(
                text,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,
                device=self.device
            )
        return embedding.astype(np.float32)

    def embed_batch(self, texts: List[str], batch_size: int = DEFAULT_BATCH_SIZE) -> np.ndarray:
        """
        Embeds a list of texts in sequential small batches on CPU.
        Prints/logs progress for each batch.
        """
        if not texts:
            return np.empty((0, self.embedding_dimension), dtype=np.float32)

        total = len(texts)
        all_embeddings = []
        total_batches = (total + batch_size - 1) // batch_size

        logger.info(f"Starting CPU embedding generation for {total} texts across {total_batches} batches (batch_size={batch_size})")

        with torch.inference_mode():
            for idx in range(0, total, batch_size):
                batch_num = (idx // batch_size) + 1
                batch_texts = texts[idx:idx + batch_size]
                logger.info(f"Embedding batch {batch_num}/{total_batches} ({len(batch_texts)} items)")

                batch_emb = self.model.encode(
                    batch_texts,
                    show_progress_bar=False,
                    batch_size=len(batch_texts),
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    device=self.device
                )
                all_embeddings.append(batch_emb)

        result = np.vstack(all_embeddings).astype(np.float32)
        return result

def compute_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Computes cosine similarity between two 1D normalized numpy vectors.
    """
    if vec1 is None or vec2 is None:
        return 0.0
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (norm1 * norm2))

# Helper getter for singleton instance
def get_cpu_embedder() -> CPUMaterialEmbedder:
    return CPUMaterialEmbedder()
