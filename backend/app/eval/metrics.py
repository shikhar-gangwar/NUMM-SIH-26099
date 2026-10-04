from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

MERGEABLE_RELATIONSHIPS = {"EXACT_DUPLICATE", "NEAR_DUPLICATE", "FUNCTIONALLY_EQUIVALENT", "COMPATIBLE"}

@dataclass
class EvalReportDTO:
    generated_at: str
    dataset: str  # SYNTHETIC or ADJUDICATED
    total_pairs_evaluated: int
    precision: float
    recall: float
    f1: float
    false_positives: int
    false_negatives: int
    fp_rate: float
    fn_rate: float
    unknown_compliance_rate: float
    critical_conflict_pass_rate: float
    veto_88_vs_109_pass_rate: float
    semantic_trap_pass_rate: float
    unsafe_auto_accepts: int
    confusion_matrix: dict[str, dict[str, int]]
    versions: dict[str, Any]

def compute_eval_metrics(
    eval_pairs: list[dict],
    dataset_name: str = "SYNTHETIC",
    versions: dict[str, Any] | None = None
) -> EvalReportDTO:
    """
    Computes rigorous evaluation metrics from a list of evaluated pairs against ground truth labels.
    Each pair dict must contain:
      - 'expected_relationship': str
      - 'predicted_relationship': str
      - 'is_88_109_trap': bool (optional)
      - 'is_unknown_trap': bool (optional)
      - 'is_semantic_trap': bool (optional)
      - 'auto_accepted': bool (optional)
    """
    total = len(eval_pairs)
    if total == 0:
        return EvalReportDTO(
            generated_at=datetime.now(timezone.utc).isoformat(),
            dataset=dataset_name,
            total_pairs_evaluated=0,
            precision=1.0,
            recall=1.0,
            f1=1.0,
            false_positives=0,
            false_negatives=0,
            fp_rate=0.0,
            fn_rate=0.0,
            unknown_compliance_rate=1.0,
            critical_conflict_pass_rate=1.0,
            veto_88_vs_109_pass_rate=1.0,
            semantic_trap_pass_rate=1.0,
            unsafe_auto_accepts=0,
            confusion_matrix={},
            versions=versions or {}
        )

    tp = 0
    fp = 0
    fn = 0
    tn = 0

    confusion: dict[str, dict[str, int]] = {}

    trap_88_total = 0
    trap_88_passed = 0

    unknown_total = 0
    unknown_passed = 0

    semantic_trap_total = 0
    semantic_trap_passed = 0

    critical_conflict_total = 0
    critical_conflict_passed = 0

    unsafe_auto_accepts = 0

    for item in eval_pairs:
        expected = item.get("expected_relationship", "NOT_EQUIVALENT").upper()
        predicted = item.get("predicted_relationship", "NOT_EQUIVALENT").upper()
        
        is_expected_mergeable = expected in MERGEABLE_RELATIONSHIPS
        is_predicted_mergeable = predicted in MERGEABLE_RELATIONSHIPS

        # Update confusion matrix
        if expected not in confusion:
            confusion[expected] = {}
        confusion[expected][predicted] = confusion[expected].get(predicted, 0) + 1

        # Binary confusion metrics
        if is_expected_mergeable and is_predicted_mergeable:
            tp += 1
        elif not is_expected_mergeable and is_predicted_mergeable:
            fp += 1
        elif is_expected_mergeable and not is_predicted_mergeable:
            fn += 1
        else:
            tn += 1

        # Trap case 8.8 vs 10.9 check
        if item.get("is_88_109_trap"):
            trap_88_total += 1
            if predicted in ["NOT_EQUIVALENT", "REVIEW_REQUIRED"]:
                trap_88_passed += 1

        # Unknown case check
        if item.get("is_unknown_trap") or expected in ["UNKNOWN", "REVIEW_REQUIRED"]:
            unknown_total += 1
            if predicted in ["UNKNOWN", "REVIEW_REQUIRED"]:
                unknown_passed += 1

        # False Semantic Trap check
        if item.get("is_semantic_trap"):
            semantic_trap_total += 1
            if predicted in ["NOT_EQUIVALENT", "REVIEW_REQUIRED", "RELATED"]:
                semantic_trap_passed += 1

        # Critical Conflict check
        if expected == "NOT_EQUIVALENT":
            critical_conflict_total += 1
            if predicted in ["NOT_EQUIVALENT", "REVIEW_REQUIRED"]:
                critical_conflict_passed += 1

        # Unsafe auto-accept check
        auto_acc = item.get("auto_accepted", False)
        if auto_acc and not is_expected_mergeable:
            unsafe_auto_accepts += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    fp_rate = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fn_rate = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    veto_88_pass_rate = (trap_88_passed / trap_88_total) if trap_88_total > 0 else 1.0
    unknown_compliance = (unknown_passed / unknown_total) if unknown_total > 0 else 1.0
    semantic_trap_pass_rate = (semantic_trap_passed / semantic_trap_total) if semantic_trap_total > 0 else 1.0
    critical_conflict_pass_rate = (critical_conflict_passed / critical_conflict_total) if critical_conflict_total > 0 else 1.0

    return EvalReportDTO(
        generated_at=datetime.now(timezone.utc).isoformat(),
        dataset=dataset_name,
        total_pairs_evaluated=total,
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1=round(f1, 4),
        false_positives=fp,
        false_negatives=fn,
        fp_rate=round(fp_rate, 4),
        fn_rate=round(fn_rate, 4),
        unknown_compliance_rate=round(unknown_compliance, 4),
        critical_conflict_pass_rate=round(critical_conflict_pass_rate, 4),
        veto_88_vs_109_pass_rate=round(veto_88_pass_rate, 4),
        semantic_trap_pass_rate=round(semantic_trap_pass_rate, 4),
        unsafe_auto_accepts=unsafe_auto_accepts,
        confusion_matrix=confusion,
        versions=versions or {}
    )
