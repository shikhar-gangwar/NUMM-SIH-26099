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
