from app.config_loader.loader import load_config_bundle

def test_load_config_bundle(db_session):
    bundle = load_config_bundle(db=db_session)
    assert bundle.scoring is not None
    assert "weights" in bundle.scoring
    assert "BOLT" in bundle.category_packs
    assert "PIPE" in bundle.category_packs
    assert bundle.abbreviations.get("SS") == "STAINLESS STEEL"
