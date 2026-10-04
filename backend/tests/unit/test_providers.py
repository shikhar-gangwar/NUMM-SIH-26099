from app.ai.providers.fake_providers import FakeEmbedding, FakeLLM
from app.ai.providers.tfidf import TfidfEmbedding
from app.ai.providers.none_llm import NoneLLM

def test_fake_embedding():
    provider = FakeEmbedding(dimension=384)
    fp = provider.fingerprint()
    assert fp.provider == "fake"
    assert fp.dimension == 384
    
    vecs = provider.embed_documents(["HEX BOLT M10X50 SS304", "PIPE 2 INCH SCH 40"])
    assert len(vecs) == 2
    assert len(vecs[0]) == 384

def test_tfidf_embedding():
    provider = TfidfEmbedding(dimension=384)
    vecs = provider.embed_documents(["BOLT HEX M10", "VALVE GATE 4 INCH"])
    assert len(vecs) == 2
    assert len(vecs[0]) == 384

def test_none_llm():
    provider = NoneLLM()
    res = provider.complete_json("extract", {}, {})
    assert res["status"] == "LLM_PROVIDER_NONE"

def test_qwen3_embedding():
    from app.ai.providers.qwen import Qwen3EmbeddingProvider
    provider = Qwen3EmbeddingProvider(dimension=1024)
    fp = provider.fingerprint()
    assert fp.provider == "qwen"
    assert fp.dimension == 1024
    assert fp.model_id == "Qwen/Qwen3-Embedding-0.6B"
    
    vecs = provider.embed_documents(["HEX BOLT M12X60 8.8", "HEX BOLT M12X60 10.9"])
    assert len(vecs) == 2
    assert len(vecs[0]) == 1024
    assert len(vecs[1]) == 1024

def test_qwen3_reranker():
    from app.ai.providers.qwen import Qwen3RerankerProvider
    reranker = Qwen3RerankerProvider()
    fp = reranker.fingerprint()
    assert fp.provider == "qwen-reranker"
    assert fp.model_id == "Qwen/Qwen3-Reranker-0.6B"
    
    scores = reranker.score_pairs([
        ("HEX BOLT M12 X 60 GRADE 8.8", "HEX BOLT M12X60 8.8"),
        ("HEX BOLT M12 X 60 GRADE 8.8", "SEAMLESS PIPE 2 INCH SCH 40")
    ])
    assert len(scores) == 2
    assert scores[0] > scores[1]  # Exact bolt query scores higher than unrelated pipe

def test_bge_m3_embedding():
    from app.ai.providers.bge import BGEM3EmbeddingProvider
    provider = BGEM3EmbeddingProvider(dimension=1024)
    fp = provider.fingerprint()
    assert fp.provider == "bge"
    assert fp.dimension == 1024
    assert fp.model_id == "BAAI/bge-m3"

    vecs = provider.embed_documents(["SEAMLESS CARBON STEEL PIPE 2 INCH SCH 40"])
    assert len(vecs) == 1
    assert len(vecs[0]) == 1024

    sparse = provider.compute_sparse_weights(["SEAMLESS CARBON STEEL PIPE 2 INCH SCH 40"])
    assert len(sparse) == 1
    assert "pipe" in sparse[0]
    assert sparse[0]["pipe"] > 0.0

