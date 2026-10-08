import pytest
from app.eval.metrics import compute_eval_metrics

def test_eval_metrics_perfect_scores():
    pairs = [
        {"expected_relationship": "FUNCTIONALLY_EQUIVALENT", "predicted_relationship": "FUNCTIONALLY_EQUIVALENT"},
        {"expected_relationship": "NOT_EQUIVALENT", "predicted_relationship": "NOT_EQUIVALENT", "is_88_109_trap": True},
        {"expected_relationship": "REVIEW_REQUIRED", "predicted_relationship": "REVIEW_REQUIRED", "is_unknown_trap": True},
        {"expected_relationship": "NOT_EQUIVALENT", "predicted_relationship": "NOT_EQUIVALENT", "is_semantic_trap": True}
    ]
    report = compute_eval_metrics(pairs, dataset_name="UNIT_TEST")
    assert report.total_pairs_evaluated == 4
    assert report.precision == 1.0
    assert report.recall == 1.0
    assert report.f1 == 1.0
    assert report.false_positives == 0
    assert report.false_negatives == 0
    assert report.veto_88_vs_109_pass_rate == 1.0
    assert report.unknown_compliance_rate == 1.0
    assert report.semantic_trap_pass_rate == 1.0
    assert report.unsafe_auto_accepts == 0

def test_eval_metrics_unsafe_auto_accept_detection():
    pairs = [
        {"expected_relationship": "NOT_EQUIVALENT", "predicted_relationship": "EXACT_DUPLICATE", "auto_accepted": True}
    ]
    report = compute_eval_metrics(pairs, dataset_name="UNIT_TEST")
    assert report.unsafe_auto_accepts == 1
    assert report.precision == 0.0
