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

def test_trap_01_true_equivalent():
    mat_a = _build_mat("HEX BOLT M12 X 60 SS316 10.9", "BOLT")
    mat_b = _build_mat("BOLT HEX M12X60 SS 316 GR10.9", "BOLT")
    res = evaluate_material_pair(mat_a, mat_b)
    assert res.relationship in ["FUNCTIONALLY_EQUIVALENT", "EXACT_DUPLICATE", "NEAR_DUPLICATE"]
    assert res.equivalence_confidence > 0.70
    assert not res.veto["applied"]

def test_trap_02_veto_88_vs_109():
    mat_a = _build_mat("HEX BOLT M12 X 60 SS316 8.8", "BOLT")
    mat_b = _build_mat("HEX BOLT M12 X 60 SS316 10.9", "BOLT")
    res = evaluate_material_pair(mat_a, mat_b, semantic_score_override=0.98)
    assert res.relationship == "NOT_EQUIVALENT"
    assert res.equivalence_confidence == 0.0
    assert res.veto["applied"] is True
    assert "property_class" in res.veto["conflicting_attributes"]

def test_trap_03_unknown_missing_grade():
    mat_a = _build_mat("HEX BOLT M12 X 60 SS", "BOLT")
    mat_b = _build_mat("HEX BOLT M12 X 60 SS316 10.9", "BOLT")
    res = evaluate_material_pair(mat_a, mat_b)
    assert res.relationship == "REVIEW_REQUIRED"
    assert res.veto["applied"] is True
    assert res.veto["gate_id"] == "G4"

def test_trap_04_compatible_standard():
    mat_a = _build_mat("HEX BOLT M10 X 50 SS304 GR 8.8 IS 1363", "BOLT")
    mat_b = _build_mat("HEXAGON HEAD BOLT M10 X 50 STAINLESS STEEL 304 GRADE 8.8 ISO 4016", "BOLT")
    res = evaluate_material_pair(mat_a, mat_b)
    assert res.relationship in ["FUNCTIONALLY_EQUIVALENT", "COMPATIBLE"]
    assert not res.veto["applied"]

def test_trap_05_related_length():
    mat_a = _build_mat("HEX BOLT M12 X 50 SS316 10.9", "BOLT")
    mat_b = _build_mat("HEX BOLT M12 X 60 SS316 10.9", "BOLT")
    res = evaluate_material_pair(mat_a, mat_b)
    assert res.relationship == "RELATED"

def test_trap_06a_pipe_sch():
    mat_a = _build_mat("PIPE 4 IN SCH 40 SEAMLESS A106 GR B", "PIPE")
    mat_b = _build_mat("PIPE 4 IN SCH 80 SEAMLESS A106 GR B", "PIPE")
    res = evaluate_material_pair(mat_a, mat_b, semantic_score_override=0.96)
    assert res.relationship == "NOT_EQUIVALENT"
    assert res.veto["applied"] is True

def test_trap_06b_brg_seal():
    mat_a = _build_mat("BEARING 6205-2RS C3", "BEARING")
    mat_b = _build_mat("BEARING 6205-ZZ C3", "BEARING")
    res = evaluate_material_pair(mat_a, mat_b, semantic_score_override=0.95)
    assert res.relationship == "NOT_EQUIVALENT"
    assert res.veto["applied"] is True

def test_trap_06c_vlv_class():
    mat_a = _build_mat("VALVE GATE 4 IN CLASS 150 SS304 FLANGED", "VALVE")
    mat_b = _build_mat("VALVE GATE 4 IN CLASS 300 SS304 FLANGED", "VALVE")
    res = evaluate_material_pair(mat_a, mat_b, semantic_score_override=0.97)
    assert res.relationship == "NOT_EQUIVALENT"
    assert res.veto["applied"] is True

def test_trap_06d_cbl_cores():
    mat_a = _build_mat("CABLE 4C X 16 SQMM COPPER XLPE 1.1KV ARMOURED", "CABLE")
    mat_b = _build_mat("CABLE 3.5C X 16 SQMM COPPER XLPE 1.1KV ARMOURED", "CABLE")
    res = evaluate_material_pair(mat_a, mat_b)
    assert res.relationship == "RELATED"
