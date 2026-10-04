import pytest
from app.normalization.text import normalize_text
from app.extraction.extractor import detect_category, extract_attributes
from app.matching.engine import evaluate_material_pair

def _build_mat(desc: str, cat_hint: str = "BOLT"):
    norm = normalize_text(desc).text
    cat = detect_category(norm, cat_hint)
    raw_attrs = extract_attributes(norm, cat)
    attrs = [
        {
            "key": a.key, "raw_text": a.raw_text, "value_text": a.value_text, "value_num": a.value_num,
            "canonical_value": a.canonical_value, "assumed": a.assumed, "internal_conflict": a.internal_conflict
        } for a in raw_attrs
    ]
    return {
        "raw_description": desc,
        "normalized_text": norm,
        "category": cat,
        "attributes": attrs
    }

def test_regression_01_true_conflict():
    """True conflict: 8.8 vs 10.9 must be G2 CRITICAL CONFLICT, NOT_EQUIVALENT, confidence 0.00."""
    mat_a = _build_mat("HEX BOLT M12 X 60 SS316 8.8", "BOLT")
    mat_b = _build_mat("HEX BOLT M12 X 60 SS316 10.9", "BOLT")
    res = evaluate_material_pair(mat_a, mat_b)
    
    assert res.relationship == "NOT_EQUIVALENT"
    assert res.equivalence_confidence == 0.0
    assert res.veto["applied"] is True
    assert res.veto.get("is_conflict") is True
    assert res.veto.get("is_unknown") is False
    assert res.veto["gate_id"] == "G2"
    assert "property_class" in res.veto["conflicting_attributes"]

def test_regression_02_true_unknown():
    """True unknown: Missing property_class must be G4 REVIEW_REQUIRED, never CRITICAL CONFLICT."""
    mat_a = _build_mat("HEX BOLT M12 X 60 SS316", "BOLT")
    mat_b = _build_mat("HEX BOLT M12 X 60 SS316 10.9", "BOLT")
    res = evaluate_material_pair(mat_a, mat_b)
    
    assert res.relationship == "REVIEW_REQUIRED"
    assert res.veto["applied"] is True
    assert res.veto.get("is_conflict") is False
    assert res.veto.get("is_unknown") is True
    assert res.veto["gate_id"] == "G4"
    assert "property_class" in res.veto.get("unknown_attributes", []) or "property_class" in res.veto.get("reason", "")

def test_regression_03_true_equivalence():
    """True equivalence: Compatible technical attributes must pass with high confidence and no veto."""
    mat_a = _build_mat("HEX BOLT M12 X 60 SS316 ISO 4014 10.9", "BOLT")
    mat_b = _build_mat("HEXAGONAL HEAD BOLT M12X60 SS 316 ISO4014 GRADE 10.9", "BOLT")
    res = evaluate_material_pair(mat_a, mat_b)
    
    assert res.relationship in ["FUNCTIONALLY_EQUIVALENT", "EXACT_DUPLICATE", "NEAR_DUPLICATE"]
    assert res.equivalence_confidence >= 0.70
    assert res.veto["applied"] is False
    assert res.veto.get("is_conflict") is False
    assert res.veto.get("is_unknown") is False

def test_regression_04_conflict_with_high_semantic_similarity():
    """High semantic similarity (0.99) MUST NOT bypass G2 property class conflict."""
    mat_a = _build_mat("HEX BOLT M12 X 60 SS316 8.8", "BOLT")
    mat_b = _build_mat("HEX BOLT M12 X 60 SS316 10.9", "BOLT")
    res = evaluate_material_pair(mat_a, mat_b, semantic_score_override=0.99)
    
    assert res.relationship == "NOT_EQUIVALENT"
    assert res.equivalence_confidence == 0.0
    assert res.veto["applied"] is True
    assert res.veto.get("is_conflict") is True
    assert res.veto["gate_id"] == "G2"

def test_regression_05_unknown_with_high_semantic_similarity():
    """High semantic similarity (0.98) MUST NOT auto-accept when critical attribute is unknown."""
    mat_a = _build_mat("HEX BOLT M12 X 60 SS316", "BOLT")
    mat_b = _build_mat("HEX BOLT M12 X 60 SS316 10.9", "BOLT")
    res = evaluate_material_pair(mat_a, mat_b, semantic_score_override=0.98)
    
    assert res.relationship == "REVIEW_REQUIRED"
    assert res.veto["applied"] is True
    assert res.veto.get("is_unknown") is True
    assert res.veto.get("is_conflict") is False
    assert res.veto["gate_id"] == "G4"
