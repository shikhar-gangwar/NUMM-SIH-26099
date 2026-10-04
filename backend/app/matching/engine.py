from dataclasses import dataclass, field
from typing import Any
import re
from app.config_loader.loader import load_config_bundle
from app.matching.comparators import compare_attribute_lists, AttributeVerdict
from app.matching.veto import evaluate_veto_lattice, VetoDecision

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None

@dataclass
class PairResult:
    material_a_id: str | None
    material_b_id: str | None
    relationship: str  # EXACT_DUPLICATE, NEAR_DUPLICATE, FUNCTIONALLY_EQUIVALENT, COMPATIBLE, RELATED, NOT_EQUIVALENT, REVIEW_REQUIRED
    equivalence_confidence: float  # 0.0 to 1.0 (0 if vetoed)
    raw_score: float
    signals: dict[str, float]  # S, L, A, C
    gates: list[dict]
    attribute_verdicts: list[dict]
    veto: dict
    explanation: str
    degraded: bool = False

def calculate_semantic_score(text_a: str, text_b: str) -> float:
    # Basic clean token overlap / semantic fallback if vector model isn't run inline
    clean_a = set(re.findall(r"\w+", text_a.upper()))
    clean_b = set(re.findall(r"\w+", text_b.upper()))
    if not clean_a or not clean_b:
        return 0.0
    inter = clean_a.intersection(clean_b)
    union = clean_a.union(clean_b)
    jaccard = len(inter) / len(union)
    
    # Check numbers match for high baseline
    num_a = set(re.findall(r"\d+", text_a))
    num_b = set(re.findall(r"\d+", text_b))
    num_match = (len(num_a.intersection(num_b)) / max(1, len(num_a.union(num_b)))) if num_a or num_b else 1.0
    
    # Trap case simulation: "HEX BOLT M12 X 60 SS316 10.9" vs "HEX BOLT M12 X 60 SS316 8.8"
    # Semantic text models give high similarity (~0.92+) despite property class difference!
    sem = 0.5 + 0.5 * jaccard
    if num_a and num_b and len(num_a.intersection(num_b)) >= max(len(num_a), len(num_b)) - 1:
        sem = max(sem, 0.90)
    return round(min(1.0, sem), 4)

def calculate_lexical_score(text_a: str, text_b: str) -> float:
    clean_a = text_a.upper().strip()
    clean_b = text_b.upper().strip()
    if clean_a == clean_b:
        return 1.0
        
    if fuzz:
        token_set = fuzz.token_set_ratio(clean_a, clean_b) / 100.0
    else:
        tokens_a = set(clean_a.split())
        tokens_b = set(clean_b.split())
        token_set = len(tokens_a.intersection(tokens_b)) / max(1, len(tokens_a.union(tokens_b)))

    # Numeric token overlap
    num_a = set(re.findall(r"\d+(?:\.\d+)?", clean_a))
    num_b = set(re.findall(r"\d+(?:\.\d+)?", clean_b))
    num_overlap = (len(num_a.intersection(num_b)) / max(1, len(num_a.union(num_b)))) if num_a or num_b else 1.0

    score = 0.6 * token_set + 0.4 * num_overlap
    return round(score, 4)

def calculate_attribute_score(verdicts: list[AttributeVerdict]) -> float:
    if not verdicts:
        return 0.5
    tier_weights = {"CRITICAL": 5.0, "MAJOR": 2.0, "MINOR": 1.0}
    verdict_scores = {"MATCH": 1.0, "COMPATIBLE": 0.85, "UNKNOWN": 0.0, "CONFLICT": 0.0}
    
    weighted_sum = 0.0
    total_weight = 0.0
    for v in verdicts:
        w = tier_weights.get(v.tier, 1.0)
        s = verdict_scores.get(v.verdict, 0.0)
        weighted_sum += w * s
        total_weight += w

    if total_weight == 0:
        return 0.0
    return round(weighted_sum / total_weight, 4)

def evaluate_material_pair(
    material_a: dict,
    material_b: dict,
    semantic_score_override: float | None = None
) -> PairResult:
    bundle = load_config_bundle()
    scoring_cfg = bundle.scoring.get("weights", {"attribute": 0.55, "semantic": 0.20, "lexical": 0.15, "category": 0.10})
    
    cat_a = material_a.get("category_code") or material_a.get("category") or "UNCLASSIFIED"
    cat_b = material_b.get("category_code") or material_b.get("category") or "UNCLASSIFIED"
    cat_conf_a = float(material_a.get("category_confidence", 1.0))
    cat_conf_b = float(material_b.get("category_confidence", 1.0))

    text_a = material_a.get("normalized_text") or material_a.get("raw_description") or ""
    text_b = material_b.get("normalized_text") or material_b.get("raw_description") or ""

    uom_dim_a = material_a.get("uom_dimension") or material_a.get("uom", {}).get("dimension") if isinstance(material_a.get("uom"), dict) else None
    uom_dim_b = material_b.get("uom_dimension") or material_b.get("uom", {}).get("dimension") if isinstance(material_b.get("uom"), dict) else None

    # Load Category Pack
    pack_config = bundle.category_packs.get(cat_a, {}) if cat_a == cat_b else {}
    identity_keys = pack_config.get("identity_required", [])

    # Extract/Compare attributes
    attrs_a = material_a.get("attributes", [])
    attrs_b = material_b.get("attributes", [])
    verdicts = compare_attribute_lists(attrs_a, attrs_b, pack_config)

    # Signals
    s_score = semantic_score_override if semantic_score_override is not None else calculate_semantic_score(text_a, text_b)
    l_score = calculate_lexical_score(text_a, text_b)
    a_score = calculate_attribute_score(verdicts)
    c_score = 1.0 if (cat_a == cat_b and cat_conf_a >= 0.8 and cat_conf_b >= 0.8) else (0.5 if cat_a == cat_b else 0.0)

    w_a = scoring_cfg.get("attribute", 0.55)
    w_s = scoring_cfg.get("semantic", 0.20)
    w_l = scoring_cfg.get("lexical", 0.15)
    w_c = scoring_cfg.get("category", 0.10)

    raw_score = round(w_a * a_score + w_s * s_score + w_l * l_score + w_c * c_score, 4)

    # Veto Lattice evaluation
    veto = evaluate_veto_lattice(
        category_a=cat_a,
        category_b=cat_b,
        cat_conf_a=cat_conf_a,
        cat_conf_b=cat_conf_b,
        uom_dim_a=uom_dim_a,
        uom_dim_b=uom_dim_b,
        attribute_verdicts=verdicts,
        identity_required_keys=identity_keys,
        degraded=False
    )

    # Determine final relationship
    if veto.applied:
        relationship = veto.relationship_ceiling or "NOT_EQUIVALENT"
        confidence = 0.0 if relationship in ["NOT_EQUIVALENT", "RELATED"] else (raw_score if relationship == "REVIEW_REQUIRED" else 0.0)
        if relationship == "NOT_EQUIVALENT":
            explanation = f"CRITICAL CONFLICT (Blocked by {veto.gate_id}): {veto.reason}"
        elif relationship == "REVIEW_REQUIRED":
            explanation = f"REVIEW REQUIRED (Gate {veto.gate_id}): {veto.reason}. Critical technical information missing or unverified."
        else:
            explanation = f"Restricted by {veto.gate_id}: {veto.reason}"
    else:
        # Check text exactness / duplicate thresholds per ARCHITECT.md §22.4
        if text_a.strip().upper() == text_b.strip().upper() or (raw_score >= 0.95 and a_score == 1.0):
            relationship = "EXACT_DUPLICATE"
        elif raw_score >= 0.88 and a_score >= 0.90 and l_score >= 0.85:
            relationship = "NEAR_DUPLICATE"
        elif raw_score >= 0.75 and a_score >= 0.75:
            relationship = "FUNCTIONALLY_EQUIVALENT"
        elif raw_score >= 0.65 and a_score >= 0.60:
            relationship = "COMPATIBLE"
        elif raw_score >= 0.50:
            relationship = "RELATED"
        else:
            relationship = "NOT_EQUIVALENT"
        confidence = raw_score
        explanation = f"Evaluated with raw score {raw_score:.2f} (Attr: {a_score:.2f}, Sem: {s_score:.2f}, Lex: {l_score:.2f})"

    return PairResult(
        material_a_id=material_a.get("id"),
        material_b_id=material_b.get("id"),
        relationship=relationship,
        equivalence_confidence=confidence,
        raw_score=raw_score,
        signals={"S": s_score, "L": l_score, "A": a_score, "C": c_score},
        gates=[{"gate_id": g.gate_id, "passed": g.passed, "reason": g.reason} for g in veto.gates],
        attribute_verdicts=[{
            "key": v.key, "tier": v.tier, "a_value": str(v.a_value), "b_value": str(v.b_value),
            "verdict": v.verdict, "variant_axis": v.variant_axis, "rule_id": v.rule_id
        } for v in verdicts],
        veto={
            "applied": veto.applied,
            "gate_id": veto.gate_id,
            "reason": veto.reason,
            "is_conflict": (relationship == "NOT_EQUIVALENT"),
            "is_unknown": (relationship == "REVIEW_REQUIRED"),
            "conflicting_attributes": veto.conflicting_attributes,
            "unknown_attributes": veto.unknown_attributes
        },
        explanation=explanation
    )
