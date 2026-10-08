import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.abspath("backend"))

from app.core.config import settings
from app.config_loader.loader import load_config_bundle
from app.ai.providers.fake_providers import FakeEmbedding, FakeLLM
from app.ai.providers.tfidf import TfidfEmbedding
from app.ai.providers.none_llm import NoneLLM
from app.audit.hash_chain import compute_audit_hash, GENESIS_HASH

def test_m1_components():
    print("Testing M1 Foundation Components...")
    
    # 1. Config Loader
    bundle = load_config_bundle()
    assert bundle.scoring is not None, "Scoring config missing"
    assert "BOLT" in bundle.category_packs, "BOLT pack missing"
    assert "PIPE" in bundle.category_packs, "PIPE pack missing"
    assert bundle.abbreviations.get("SS") == "STAINLESS STEEL", "Abbreviation SS missing"
    print("[OK] Config Loader & Packs: OK")
    
    # 2. AI Providers
    fake_emb = FakeEmbedding(dimension=384)
    vecs = fake_emb.embed_documents(["BOLT HEX M10X50 SS304", "PIPE 2 INCH SCH 40"])
    assert len(vecs) == 2 and len(vecs[0]) == 384, "Fake embedding failed"
    
    tfidf_emb = TfidfEmbedding(dimension=384)
    t_vecs = tfidf_emb.embed_documents(["BOLT HEX M10", "VALVE GATE 4 INCH"])
    assert len(t_vecs) == 2 and len(t_vecs[0]) == 384, "TF-IDF embedding failed"
    
    none_llm = NoneLLM()
    assert none_llm.fingerprint().provider == "none", "NoneLLM failed"
    print("[OK] AI Provider Layer & Fingerprints: OK")
    
    # 3. Audit Hash Chain
    h1 = compute_audit_hash(GENESIS_HASH, {"seq": 1, "action": "INIT"})
    assert len(h1) == 64, "Audit hash length invalid"
    print("[OK] Audit Hash Chain Calculation: OK")
    
    print("\nALL M1 VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_m1_components()
