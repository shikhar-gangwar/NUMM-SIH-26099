from dataclasses import dataclass, field
from app.matching.comparators import AttributeVerdict

@dataclass
class GateResult:
    gate_id: str
    passed: bool
    decisive: bool = False
    relationship_ceiling: str | None = None  # NOT_EQUIVALENT, RELATED, REVIEW_REQUIRED, etc.
    reason: str | None = None

@dataclass
class VetoDecision:
    applied: bool = False
    gate_id: str | None = None
    relationship_ceiling: str | None = None
    reason: str | None = None
    conflicting_attributes: list[str] = field(default_factory=list)
    unknown_attributes: list[str] = field(default_factory=list)
    gates: list[GateResult] = field(default_factory=list)

def evaluate_veto_lattice(
    category_a: str,
    category_b: str,
    cat_conf_a: float,
    cat_conf_b: float,
    uom_dim_a: str | None,
    uom_dim_b: str | None,
    attribute_verdicts: list[AttributeVerdict],
    identity_required_keys: list[str] | None = None,
    degraded: bool = False
) -> VetoDecision:
    decision = VetoDecision()
    
    # G1: Category gate
    if cat_conf_a >= 0.8 and cat_conf_b >= 0.8 and category_a != category_b:
        gate_g1 = GateResult(
            gate_id="G1",
            passed=False,
            decisive=True,
            relationship_ceiling="NOT_EQUIVALENT",
            reason=f"Category mismatch: {category_a} vs {category_b}"
        )
        decision.gates.append(gate_g1)
        decision.applied = True
        decision.gate_id = "G1"
        decision.relationship_ceiling = "NOT_EQUIVALENT"
        decision.reason = gate_g1.reason
        return decision
    else:
        decision.gates.append(GateResult(gate_id="G1", passed=True))

    # Collect conflicts and unknowns by tier
    critical_conflicts = [v for v in attribute_verdicts if v.tier == "CRITICAL" and v.verdict == "CONFLICT"]
    critical_unknowns = [v for v in attribute_verdicts if v.tier == "CRITICAL" and v.verdict == "UNKNOWN"]
    
    # G2: Critical conflict veto gate
    if critical_conflicts:
        all_variant_axis = all(v.variant_axis for v in critical_conflicts)
        non_conflict_criticals = [v for v in attribute_verdicts if v.tier == "CRITICAL" and v.verdict != "CONFLICT"]
        other_criticals_ok = all(v.verdict in ["MATCH", "COMPATIBLE"] for v in non_conflict_criticals)
        
        if all_variant_axis and other_criticals_ok:
            gate_g2 = GateResult(
                gate_id="G2",
                passed=False,
                decisive=True,
                relationship_ceiling="RELATED",
                reason=f"Variant axis conflict on critical attributes: {[v.key for v in critical_conflicts]}"
            )
            decision.relationship_ceiling = "RELATED"
        else:
            gate_g2 = GateResult(
                gate_id="G2",
                passed=False,
                decisive=True,
                relationship_ceiling="NOT_EQUIVALENT",
                reason=f"Critical attribute conflict: {[f'{v.key} ({v.a_value} != {v.b_value})' for v in critical_conflicts]}"
            )
            decision.relationship_ceiling = "NOT_EQUIVALENT"
            
        decision.gates.append(gate_g2)
        decision.applied = True
        decision.gate_id = "G2"
        decision.reason = gate_g2.reason
        decision.conflicting_attributes = [v.key for v in critical_conflicts]
        return decision
    else:
        decision.gates.append(GateResult(gate_id="G2", passed=True))

    # G3: UOM dimension mismatch gate
    if uom_dim_a and uom_dim_b and uom_dim_a != uom_dim_b and uom_dim_a != "COUNT" and uom_dim_b != "COUNT":
        gate_g3 = GateResult(
            gate_id="G3",
            passed=False,
            decisive=True,
            relationship_ceiling="NOT_EQUIVALENT",
            reason=f"UOM dimension mismatch: {uom_dim_a} vs {uom_dim_b}"
        )
        decision.gates.append(gate_g3)
        decision.applied = True
        decision.gate_id = "G3"
        decision.relationship_ceiling = "NOT_EQUIVALENT"
        decision.reason = gate_g3.reason
        return decision
    else:
        decision.gates.append(GateResult(gate_id="G3", passed=True))

    # G4: Critical unknown gate
    if critical_unknowns:
        gate_g4 = GateResult(
            gate_id="G4",
            passed=False,
            decisive=True,
            relationship_ceiling="REVIEW_REQUIRED",
            reason=f"Critical attribute unknown: {[v.key for v in critical_unknowns]}"
        )
        decision.gates.append(gate_g4)
        decision.applied = True
        decision.gate_id = "G4"
        decision.relationship_ceiling = "REVIEW_REQUIRED"
        decision.reason = gate_g4.reason
        decision.unknown_attributes = [v.key for v in critical_unknowns]
        return decision
    else:
        decision.gates.append(GateResult(gate_id="G4", passed=True))

    # G5: Low classification confidence
    if cat_conf_a < 0.6 or cat_conf_b < 0.6:
        gate_g5 = GateResult(
            gate_id="G5",
            passed=False,
            decisive=True,
            relationship_ceiling="REVIEW_REQUIRED",
            reason=f"Low category classification confidence ({cat_conf_a:.2f}, {cat_conf_b:.2f})"
        )
        decision.gates.append(gate_g5)
        decision.applied = True
        decision.gate_id = "G5"
        decision.relationship_ceiling = "REVIEW_REQUIRED"
        decision.reason = gate_g5.reason
        return decision
    else:
        decision.gates.append(GateResult(gate_id="G5", passed=True))

    # G6: Degraded provider
    if degraded:
        gate_g6 = GateResult(
            gate_id="G6",
            passed=False,
            decisive=True,
            relationship_ceiling="REVIEW_REQUIRED",
            reason="AI provider degraded state"
        )
        decision.gates.append(gate_g6)
        decision.applied = True
        decision.gate_id = "G6"
        decision.relationship_ceiling = "REVIEW_REQUIRED"
        decision.reason = gate_g6.reason
        return decision
    else:
        decision.gates.append(GateResult(gate_id="G6", passed=True))

    return decision
