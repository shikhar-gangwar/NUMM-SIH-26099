#!/usr/bin/env python3
"""
M3 Verification Script — Material Intelligence, Synthetic Data & Evaluation Framework.
SIH 2026 PS 26099 — National Unified Material Master Framework.
"""

import sys
import json
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from generate_synthetic import generate_synthetic_dataset
from app.eval.evaluator import run_evaluation_on_pairs
from app.normalization.text import normalize_text
from app.extraction.extractor import detect_category, extract_attributes
from app.matching.engine import evaluate_material_pair

def _build_mat_dict(desc: str, cat_hint: str):
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

def main():
    print("==================================================")
    print("RUNNING M3 VERIFICATION — MATERIAL INTELLIGENCE & EVALUATION")
    print("==================================================")

    # 1. Deterministic Synthetic Generation
    print("\n[Step 1] Verifying Synthetic Dataset Generation...")
    m_count, pair_count = generate_synthetic_dataset(seed=42, output_dir="data/synthetic")
    assert m_count >= 1200, f"Expected >= 1200 synthetic materials, got {m_count}"
    assert pair_count >= 9, f"Expected >= 9 ground truth pairs, got {pair_count}"
    print(f"  -> Generated {m_count} synthetic materials across 5 CPSEs")
    print(f"  -> Generated {pair_count} ground-truth evaluation pairs")

    # 2. File Artifacts Check
    print("\n[Step 2] Verifying File Artifacts...")
    gt_file = Path("data/synthetic/ground_truth_pairs.json")
    all_csv = Path("data/synthetic/all_synthetic_materials.csv")
    assert gt_file.exists(), "ground_truth_pairs.json missing!"
    assert all_csv.exists(), "all_synthetic_materials.csv missing!"
    print("  -> Synthetic CSV and Ground Truth JSON files present and verified")

    # 3. Categorization & Extraction Verification across Category Packs
    print("\n[Step 3] Verifying Categorization & Attribute Extraction across 6 Category Packs...")
    sample_tests = [
        ("HEX BOLT M12 X 60 SS316 10.9", "BOLT", ["fastener_type", "nominal_diameter", "length", "property_class", "material"]),
        ("PIPE 4 IN SCH 40 SEAMLESS A106 GR B", "PIPE", ["spec_grade", "nominal_size", "schedule_or_thickness", "manufacturing"]),
        ("BEARING 6205-2RS C3", "BEARING", ["designation_base", "seal_type", "clearance"]),
        ("VALVE GATE 4 IN CLASS 150 SS304 FLANGED", "VALVE", ["valve_type", "pressure_class", "end_connection"]),
        ("GASKET SPIRAL WOUND 4 IN CLASS 300 SS304", "GASKET", ["gasket_type", "pressure_class"]),
        ("CABLE 4C X 16 SQMM COPPER XLPE 1.1KV ARMOURED", "CABLE", ["conductor_material", "voltage_grade", "cores", "cross_section"])
    ]

    for raw_desc, exp_cat, req_attrs in sample_tests:
        norm = normalize_text(raw_desc).text
        cat = detect_category(norm, exp_cat)
        assert cat == exp_cat, f"Expected category {exp_cat}, got {cat} for '{raw_desc}'"
        extracted = extract_attributes(norm, cat)
        ext_keys = [a.key for a in extracted]
        for req in req_attrs:
            assert req in ext_keys, f"Missing expected attribute '{req}' in category {cat} for '{raw_desc}'"
    print("  -> 6 Category Packs successfully validated for normalization & extraction")

    # 4. Mandatory Trap Cases Verification
    print("\n[Step 4] Verifying Mandatory AI / Matching Trap Test Cases...")
    
    # 8.8 vs 10.9 Veto Trap
    mat_88 = _build_mat_dict("HEX BOLT M12 X 60 SS316 8.8", "BOLT")
    mat_109 = _build_mat_dict("HEX BOLT M12 X 60 SS316 10.9", "BOLT")
    res_veto = evaluate_material_pair(mat_88, mat_109, semantic_score_override=0.98)
    assert res_veto.relationship == "NOT_EQUIVALENT", f"Expected NOT_EQUIVALENT for 8.8 vs 10.9, got {res_veto.relationship}"
    assert res_veto.equivalence_confidence == 0.0, f"Expected 0 confidence for veto, got {res_veto.equivalence_confidence}"
    assert res_veto.veto["applied"] is True, "Expected veto to be applied for 8.8 vs 10.9"
    print("  -> Mandatory Trap 1 (8.8 vs 10.9 Veto Gate): PASSED")

    # UNKNOWN missing property class
    mat_no_grade = _build_mat_dict("HEX BOLT M12 X 60 SS", "BOLT")
    res_unk = evaluate_material_pair(mat_no_grade, mat_109)
    assert res_unk.relationship == "REVIEW_REQUIRED", f"Expected REVIEW_REQUIRED for missing grade, got {res_unk.relationship}"
    print("  -> Mandatory Trap 2 (UNKNOWN missing critical attribute): PASSED")

    # True Equivalent
    mat_eq = _build_mat_dict("BOLT HEX M12X60 SS 316 GR10.9", "BOLT")
    res_eq = evaluate_material_pair(mat_109, mat_eq)
    assert res_eq.relationship in ["FUNCTIONALLY_EQUIVALENT", "EXACT_DUPLICATE", "NEAR_DUPLICATE"]
    print("  -> Mandatory Trap 3 (True Technical Equivalent): PASSED")

    # 5. Full Ground-Truth Evaluation Run
    print("\n[Step 5] Running Full Evaluation Framework on Ground Truth Dataset...")
    with open(gt_file, "r", encoding="utf-8") as f:
        pairs = json.load(f)
    
    report = run_evaluation_on_pairs(pairs, dataset_name="SYNTHETIC")
    print(f"  -> Precision:                     {report.precision * 100:.2f}%")
    print(f"  -> Recall:                        {report.recall * 100:.2f}%")
    print(f"  -> F1 Score:                      {report.f1 * 100:.2f}%")
    print(f"  -> 8.8 vs 10.9 Veto Pass Rate:    {report.veto_88_vs_109_pass_rate * 100:.2f}%")
    print(f"  -> UNKNOWN Compliance Rate:       {report.unknown_compliance_rate * 100:.2f}%")
    print(f"  -> Critical Conflict Pass Rate:   {report.critical_conflict_pass_rate * 100:.2f}%")
    print(f"  -> False Semantic Trap Pass Rate: {report.semantic_trap_pass_rate * 100:.2f}%")
    print(f"  -> Unsafe Auto-Accepts:           {report.unsafe_auto_accepts}")

    assert report.precision == 1.0, f"Expected 1.0 precision, got {report.precision}"
    assert report.recall == 1.0, f"Expected 1.0 recall, got {report.recall}"
    assert report.veto_88_vs_109_pass_rate == 1.0, "8.8 vs 10.9 veto pass rate must be 1.0"
    assert report.unknown_compliance_rate == 1.0, "UNKNOWN compliance rate must be 1.0"
    assert report.unsafe_auto_accepts == 0, "Unsafe auto accepts must be 0"

    print("\n==================================================")
    print("M3 VERIFICATION SUCCESSFUL — ALL GATES & METRICS PASSED!")
    print("==================================================\n")

if __name__ == "__main__":
    main()
