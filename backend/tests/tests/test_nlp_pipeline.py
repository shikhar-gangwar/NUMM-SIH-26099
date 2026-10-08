import os
import sys
import time
import pytest
import numpy as np

# Ensure backend path is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ai.nlp.normalizer import normalize_text
from app.ai.nlp.abbreviation import expand_abbreviations
from app.ai.nlp.attribute_extractor import extract_attributes
from app.ai.nlp.pipeline import nlp_pipeline
from app.ai.embeddings.embedder import get_cpu_embedder, compute_cosine_similarity
from app.ai.embeddings.cache import embedding_cache

def test_normalization():
    """1. Unit tests for text normalization & technical preservation"""
    raw_inputs = [
        "HEX BOLT M16 X 70 GRADE 10.9",
        "BALL VALVE 1 INCH CLASS 300 FLANGED SS316",
        "SEAMLESS PIPE SCH 40 ASTM A53 70 MM",
        "BEARING 6308-ZZ C3"
    ]

    for inp in raw_inputs:
        norm = normalize_text(inp)
        assert len(norm) > 0
        assert norm.isupper()
        # Verify numbers, grades, units preserved
        if "10.9" in inp:
            assert "10.9" in norm
        if "SS316" in inp:
            assert "SS316" in norm
        if "SCH 40" in inp:
            assert "SCH 40" in norm
        if "CLASS 300" in inp:
            assert "CLASS 300" in norm

def test_abbreviation_expansion():
    """Verify abbreviation expansion preserves compound tech specs like SS316"""
    # Standalone SS -> STAINLESS STEEL
    assert "STAINLESS STEEL" in expand_abbreviations("SS PIPE")

    # Compound SS316 preserved
    assert "SS316" in expand_abbreviations("VALVE SS316")
    assert "STAINLESS STEEL316" not in expand_abbreviations("VALVE SS316")

    # BRG -> BEARING, VLV -> VALVE
    assert "BEARING" in expand_abbreviations("BALL BRG 6308")
    assert "VALVE" in expand_abbreviations("BALL VLV 1 INCH")

def test_attribute_extraction():
    """2. Unit tests for deterministic attribute extraction"""
    # Case A: Bolt
    res_bolt = extract_attributes("HEX BOLT M16 X 70 GRADE 10.9")
    assert res_bolt.get("material_type") == "bolt"
    assert res_bolt.get("diameter") == "M16"
    assert res_bolt.get("length") == "70"
    assert res_bolt.get("grade") == "10.9"

    # Case B: Valve
    res_valve = extract_attributes("BALL VALVE 1 INCH CLASS 300 FLANGED SS316")
    assert res_valve.get("material_type") == "ball valve"
    assert res_valve.get("size") == "1 inch"
    assert res_valve.get("pressure_class") == "300"
    assert res_valve.get("connection_type") == "flanged"
    assert res_valve.get("material") == "SS316"

def test_embedding_generation():
    """3. Embedding generation test (CPU, 384 dimensions)"""
    embedder = get_cpu_embedder()
    text = "BOLT HEXAGONAL M16 X 70 GRADE 10.9"

    vec = embedder.embed_single(text)
    assert isinstance(vec, np.ndarray)
    assert vec.shape == (384,)
    assert vec.dtype == np.float32

    # Verify batch embedding
    texts = [
        "BOLT HEXAGONAL M16 X 70 GRADE 10.9",
        "BEARING BALL 6308 C3 SHIELDED",
        "VALVE BALL 1 INCH CLASS 300 FLANGED STAINLESS STEEL 316"
    ]
    batch_vecs = embedder.embed_batch(texts, batch_size=16)
    assert batch_vecs.shape == (3, 384)

def test_similarity_and_engineering_veto():
    """4. Similarity test demonstrating semantic similarity vs technical gate veto"""
    embedder = get_cpu_embedder()

    # Pair 1: Similar bolts with different property classes (Trap Case: 8.8 vs 10.9)
    p1_text1 = nlp_pipeline.process("HEX BOLT M16 X 70 GRADE 8.8")["normalized_text"]
    p1_text2 = nlp_pipeline.process("HEX BOLT M16 X 70 GRADE 10.9")["normalized_text"]

    v1_1 = embedder.embed_single(p1_text1)
    v1_2 = embedder.embed_single(p1_text2)
    sim1 = compute_cosine_similarity(v1_1, v1_2)

    # High semantic similarity (> 0.85) expected because words overlap almost completely
    assert sim1 > 0.80

    # BUT deterministic attribute extraction highlights property class conflict!
    attr1 = extract_attributes(p1_text1)
    attr2 = extract_attributes(p1_text2)
    assert attr1.get("grade") == "8.8"
    assert attr2.get("grade") == "10.9"
    assert attr1.get("grade") != attr2.get("grade")

    # Pair 2: Equivalent items with different word order
    p2_text1 = nlp_pipeline.process("HEX BOLT M16 X 70 GRADE 10.9")["normalized_text"]
    p2_text2 = nlp_pipeline.process("BOLT HEX M16 X 70 HIGH TENSILE")["normalized_text"]

    v2_1 = embedder.embed_single(p2_text1)
    v2_2 = embedder.embed_single(p2_text2)
    sim2 = compute_cosine_similarity(v2_1, v2_2)

    assert sim2 > 0.75

def test_cpu_caching_and_performance():
    """5. CPU performance and caching test with max record limit"""
    max_records = int(os.getenv("NLP_MAX_RECORDS", "100"))
    sample_descriptions = [
        f"TEST MATERIAL ITEM {i} M16 X 70 GRADE 10.9 SS316"
        for i in range(min(max_records, 20))
    ]

    embedder = get_cpu_embedder()
    start_time = time.time()

    processed_items = []
    for item in sample_descriptions:
        res = nlp_pipeline.process(item)
        cached = embedding_cache.get(res["text_hash"])
        if cached:
            vec = cached["embedding"]
        else:
            vec = embedder.embed_single(res["normalized_text"])
            embedding_cache.put(res["text_hash"], res["normalized_text"], vec)
        res["embedding"] = vec
        processed_items.append(res)

    duration = time.time() - start_time
    assert len(processed_items) == len(sample_descriptions)

    # Second pass should be instant due to cache hit
    start_cache_time = time.time()
    for item in sample_descriptions:
        res = nlp_pipeline.process(item)
        cached = embedding_cache.get(res["text_hash"])
        assert cached is not None
    cache_duration = time.time() - start_cache_time

    assert cache_duration < duration

if __name__ == "__main__":
    pytest.main(["-v", __file__])
