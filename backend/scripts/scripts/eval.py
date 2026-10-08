#!/usr/bin/env python3
"""
Evaluation Runner for National Unified Material Master Framework (SIH 2026 PS 26099).

Evaluates the matching engine and veto lattice on ground-truth synthetic trap pairs.
Outputs precision, recall, F1, false positives, false negatives, veto pass rates, and UNKNOWN compliance.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import json
from app.eval.evaluator import run_evaluation_on_pairs

def main():
    gt_path = Path("data/synthetic/ground_truth_pairs.json")
    if not gt_path.exists():
        print("Ground truth file not found. Generating synthetic dataset first...")
        from scripts.generate_synthetic import generate_synthetic_dataset
        generate_synthetic_dataset(seed=42)

    with open(gt_path, "r", encoding="utf-8") as f:
        pairs = json.load(f)

    print(f"Running evaluation on {len(pairs)} ground-truth pairs...")
    report = run_evaluation_on_pairs(pairs, dataset_name="SYNTHETIC")

    print("==================================================")
    print("EVALUATION METRICS REPORT — M3 MATERIAL INTELLIGENCE")
    print("==================================================")
    print(f"Dataset:                       {report.dataset}")
    print(f"Total Pairs Evaluated:         {report.total_pairs_evaluated}")
    print(f"Precision:                     {report.precision * 100:.2f}%")
    print(f"Recall:                        {report.recall * 100:.2f}%")
    print(f"F1 Score:                      {report.f1 * 100:.2f}%")
    print(f"False Positives:               {report.false_positives} (Rate: {report.fp_rate * 100:.2f}%)")
    print(f"False Negatives:               {report.false_negatives} (Rate: {report.fn_rate * 100:.2f}%)")
    print(f"8.8 vs 10.9 Veto Pass Rate:    {report.veto_88_vs_109_pass_rate * 100:.2f}%  [GATE: 100% REQUIRED]")
    print(f"UNKNOWN Compliance Rate:       {report.unknown_compliance_rate * 100:.2f}%  [GATE: 100% REQUIRED]")
    print(f"Critical Conflict Pass Rate:   {report.critical_conflict_pass_rate * 100:.2f}%")
    print(f"False Semantic Trap Pass Rate: {report.semantic_trap_pass_rate * 100:.2f}%")
    print(f"Unsafe Auto-Accepts:           {report.unsafe_auto_accepts}  [GATE: 0 ALLOWED]")
    print("==================================================\n")

    # Save report
    rep_dir = Path("reports")
    rep_dir.mkdir(exist_ok=True)
    out_file = rep_dir / "eval_latest.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": report.generated_at,
            "dataset": report.dataset,
            "total_pairs_evaluated": report.total_pairs_evaluated,
            "precision": report.precision,
            "recall": report.recall,
            "f1": report.f1,
            "false_positives": report.false_positives,
            "false_negatives": report.false_negatives,
            "fp_rate": report.fp_rate,
            "fn_rate": report.fn_rate,
            "unknown_compliance_rate": report.unknown_compliance_rate,
            "critical_conflict_pass_rate": report.critical_conflict_pass_rate,
            "veto_88_vs_109_pass_rate": report.veto_88_vs_109_pass_rate,
            "semantic_trap_pass_rate": report.semantic_trap_pass_rate,
            "unsafe_auto_accepts": report.unsafe_auto_accepts,
            "confusion_matrix": report.confusion_matrix
        }, f, indent=2)

    print(f"Report saved to {out_file}")

    if report.veto_88_vs_109_pass_rate < 1.0 or report.unsafe_auto_accepts > 0:
        print("ERROR: Mandatory evaluation gates failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
