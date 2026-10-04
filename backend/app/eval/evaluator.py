import json
from typing import Any
from app.extraction.extractor import detect_category, extract_attributes
from app.normalization.text import normalize_text, NormalizedText
from app.matching.engine import evaluate_material_pair
from app.eval.metrics import compute_eval_metrics, EvalReportDTO

def run_evaluation_on_pairs(
    pair_ground_truth: list[dict],
    materials_map: dict[str, dict] | None = None,
    dataset_name: str = "SYNTHETIC"
) -> EvalReportDTO:
    """
    Evaluates a set of labeled material pairs through the matching engine and computes performance metrics.
    """
    evaluated_results = []
    
    for pair in pair_ground_truth:
        import copy
        mat_a = copy.deepcopy(pair.get("mat_a") or pair.get("material_a") or {})
        mat_b = copy.deepcopy(pair.get("mat_b") or pair.get("material_b") or {})
        
        # Resolve from map if only IDs given
        if materials_map and isinstance(mat_a, str):
            mat_a = materials_map.get(mat_a, {"raw_description": mat_a})
        if materials_map and isinstance(mat_b, str):
            mat_b = materials_map.get(mat_b, {"raw_description": mat_b})

        # Ensure normalized text and extracted attributes exist
        if not mat_a.get("normalized_text"):
            norm_a = normalize_text(mat_a.get("raw_description", ""))
            mat_a["normalized_text"] = norm_a.text if isinstance(norm_a, NormalizedText) else str(norm_a)
        elif isinstance(mat_a["normalized_text"], NormalizedText):
            mat_a["normalized_text"] = mat_a["normalized_text"].text

        if not mat_b.get("normalized_text"):
            norm_b = normalize_text(mat_b.get("raw_description", ""))
            mat_b["normalized_text"] = norm_b.text if isinstance(norm_b, NormalizedText) else str(norm_b)
        elif isinstance(mat_b["normalized_text"], NormalizedText):
            mat_b["normalized_text"] = mat_b["normalized_text"].text

        if not mat_a.get("category"):
            mat_a["category"] = detect_category(mat_a["normalized_text"], mat_a.get("category_hint"))
        if not mat_b.get("category"):
            mat_b["category"] = detect_category(mat_b["normalized_text"], mat_b.get("category_hint"))

        if not mat_a.get("attributes"):
            raw_attrs = extract_attributes(mat_a["normalized_text"], mat_a["category"])
            mat_a["attributes"] = [
                {
                    "key": a.key, "raw_text": a.raw_text, "value_text": a.value_text, "value_num": a.value_num,
                    "canonical_value": a.canonical_value, "assumed": a.assumed, "internal_conflict": a.internal_conflict
                } for a in raw_attrs
            ]

        if not mat_b.get("attributes"):
            raw_attrs = extract_attributes(mat_b["normalized_text"], mat_b["category"])
            mat_b["attributes"] = [
                {
                    "key": a.key, "raw_text": a.raw_text, "value_text": a.value_text, "value_num": a.value_num,
                    "canonical_value": a.canonical_value, "assumed": a.assumed, "internal_conflict": a.internal_conflict
                } for a in raw_attrs
            ]

        # Evaluate through matching engine
        sem_override = pair.get("simulated_semantic_score")
        res = evaluate_material_pair(mat_a, mat_b, semantic_score_override=sem_override)

        evaluated_results.append({
            "pair_id": pair.get("id"),
            "expected_relationship": pair.get("expected_relationship"),
            "predicted_relationship": res.relationship,
            "equivalence_confidence": res.equivalence_confidence,
            "raw_score": res.raw_score,
            "is_88_109_trap": pair.get("is_88_109_trap", False),
            "is_unknown_trap": pair.get("is_unknown_trap", False),
            "is_semantic_trap": pair.get("is_semantic_trap", False),
            "auto_accepted": pair.get("auto_accepted", False)
        })

    report = compute_eval_metrics(evaluated_results, dataset_name=dataset_name)
    return report
