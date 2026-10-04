from dataclasses import dataclass
from typing import Any
import re
from app.config_loader.loader import load_config_bundle

@dataclass
class AttributeVerdict:
    key: str
    tier: str  # CRITICAL, MAJOR, MINOR
    a_value: Any
    b_value: Any
    verdict: str  # MATCH, COMPATIBLE, CONFLICT, UNKNOWN
    rule_id: str | None = None
    variant_axis: bool = False
    note: str | None = None

def _get_material_alias_group(val: str) -> str | None:
    if not val:
        return None
    clean = str(val).upper().replace("_", " ").strip()
    bundle = load_config_bundle()
    groups = bundle.material_aliases if isinstance(bundle.material_aliases, dict) else {}
    for grp_key, grp_data in groups.items():
        if isinstance(grp_data, dict):
            aliases = [str(a).upper() for a in grp_data.get("aliases", []) if a is not None]
            canon = str(grp_data.get("canonical", "")).upper()
            if clean in aliases or clean == grp_key.upper() or clean == canon:
                return grp_key
    return clean

def _normalize_standard_name(std: str) -> str:
    clean = str(std).upper().replace("-", " ").strip()
    clean = re.sub(r"\s+", " ", clean)
    return clean

def _are_standards_equivalent(std_a: str, std_b: str) -> bool:
    norm_a = _normalize_standard_name(std_a)
    norm_b = _normalize_standard_name(std_b)
    if norm_a == norm_b:
        return True
    bundle = load_config_bundle()
    equivs = bundle.standard_equiv if isinstance(bundle.standard_equiv, list) else bundle.standard_equiv.get("equivalences", []) if isinstance(bundle.standard_equiv, dict) else []
    for eq in equivs:
        if isinstance(eq, dict):
            sa = _normalize_standard_name(eq.get("standard_a", ""))
            sb = _normalize_standard_name(eq.get("standard_b", ""))
            if (norm_a == sa and norm_b == sb) or (norm_a == sb and norm_b == sa):
                return True
    return False

def _parse_pipe_size(val: Any) -> float | None:
    if val is None:
        return None
    val_str = str(val).upper().replace("INCH", "").replace("IN", "").replace('"', "").replace("DN", "").strip()
    bundle = load_config_bundle()
    sizes = bundle.size_tables if isinstance(bundle.size_tables, list) else bundle.size_tables.get("pipe_sizes", []) if isinstance(bundle.size_tables, dict) else []
    for row in sizes:
        if isinstance(row, dict):
            if val_str == str(row.get("nps")) or val_str == str(row.get("dn")) or val_str == str(row.get("od_mm")):
                return float(row.get("od_mm"))
    try:
        return float(val_str)
    except ValueError:
        return None

def compare_single_attribute(
    key: str,
    attr_def: dict,
    a_attr: Any | None,
    b_attr: Any | None
) -> AttributeVerdict:
    tier = attr_def.get("tier", "MAJOR")
    variant_axis = attr_def.get("variant_axis", False)
    comparator = attr_def.get("comparator", "EXACT_ENUM")

    # UNKNOWN handling: missing or invalid
    if a_attr is None or b_attr is None:
        return AttributeVerdict(
            key=key,
            tier=tier,
            a_value=a_attr.get("canonical_value") if isinstance(a_attr, dict) else a_attr,
            b_value=b_attr.get("canonical_value") if isinstance(b_attr, dict) else b_attr,
            verdict="UNKNOWN",
            rule_id="missing_attribute",
            variant_axis=variant_axis,
            note="One or both material attribute values are missing"
        )

    # If dict payload, unpack canonical value & check flags
    if isinstance(a_attr, dict):
        if a_attr.get("assumed") or a_attr.get("internal_conflict"):
            return AttributeVerdict(
                key=key, tier=tier, a_value=a_attr.get("canonical_value"), b_value=b_attr.get("canonical_value") if isinstance(b_attr, dict) else b_attr,
                verdict="UNKNOWN", rule_id="assumed_or_conflict", variant_axis=variant_axis, note="Attribute assumed or has internal conflict"
            )
        val_a = a_attr.get("canonical_value") or a_attr.get("value_text") or a_attr.get("value_num")
    else:
        val_a = a_attr

    if isinstance(b_attr, dict):
        if b_attr.get("assumed") or b_attr.get("internal_conflict"):
            return AttributeVerdict(
                key=key, tier=tier, a_value=val_a, b_value=b_attr.get("canonical_value"),
                verdict="UNKNOWN", rule_id="assumed_or_conflict", variant_axis=variant_axis, note="Attribute assumed or has internal conflict"
            )
        val_b = b_attr.get("canonical_value") or b_attr.get("value_text") or b_attr.get("value_num")
    else:
        val_b = b_attr

    if val_a is None or val_b is None:
        return AttributeVerdict(
            key=key, tier=tier, a_value=val_a, b_value=val_b, verdict="UNKNOWN",
            rule_id="null_value", variant_axis=variant_axis, note="Attribute value is null"
        )

    # Comparator execution
    if comparator == "EXACT_ENUM":
        str_a = str(val_a).strip().upper()
        str_b = str(val_b).strip().upper()
        if str_a == str_b:
            return AttributeVerdict(key=key, tier=tier, a_value=val_a, b_value=val_b, verdict="MATCH", rule_id="exact_enum_match", variant_axis=variant_axis)
        else:
            return AttributeVerdict(key=key, tier=tier, a_value=val_a, b_value=val_b, verdict="CONFLICT", rule_id="exact_enum_conflict", variant_axis=variant_axis)

    elif comparator == "NUMERIC_TOL":
        try:
            num_a = float(str(val_a).replace("mm", "").replace("mm2", "").strip())
            num_b = float(str(val_b).replace("mm", "").replace("mm2", "").strip())
            tol = attr_def.get("tolerance", {}).get("abs", 0.0)
            if abs(num_a - num_b) <= tol:
                return AttributeVerdict(key=key, tier=tier, a_value=val_a, b_value=val_b, verdict="MATCH", rule_id="numeric_tol_match", variant_axis=variant_axis)
            else:
                return AttributeVerdict(key=key, tier=tier, a_value=val_a, b_value=val_b, verdict="CONFLICT", rule_id="numeric_tol_conflict", variant_axis=variant_axis)
        except (ValueError, AttributeError):
            if str(val_a).strip().upper() == str(val_b).strip().upper():
                return AttributeVerdict(key=key, tier=tier, a_value=val_a, b_value=val_b, verdict="MATCH", rule_id="numeric_str_match", variant_axis=variant_axis)
            return AttributeVerdict(key=key, tier=tier, a_value=val_a, b_value=val_b, verdict="CONFLICT", rule_id="numeric_parse_conflict", variant_axis=variant_axis)

    elif comparator == "MATERIAL_EQUIV":
        group_a = _get_material_alias_group(str(val_a))
        group_b = _get_material_alias_group(str(val_b))
        str_a = str(val_a).strip().upper()
        str_b = str(val_b).strip().upper()
        if str_a == str_b:
            return AttributeVerdict(key=key, tier=tier, a_value=val_a, b_value=val_b, verdict="MATCH", rule_id="material_exact_match", variant_axis=variant_axis)
        elif group_a and group_b and group_a == group_b:
            return AttributeVerdict(key=key, tier=tier, a_value=val_a, b_value=val_b, verdict="COMPATIBLE", rule_id="material_alias_compatible", variant_axis=variant_axis, note=f"Alias group {group_a}")
        else:
            return AttributeVerdict(key=key, tier=tier, a_value=val_a, b_value=val_b, verdict="CONFLICT", rule_id="material_conflict", variant_axis=variant_axis)

    elif comparator == "STANDARD_EQUIV":
        str_a = str(val_a).strip().upper()
        str_b = str(val_b).strip().upper()
        if str_a == str_b:
            return AttributeVerdict(key=key, tier=tier, a_value=val_a, b_value=val_b, verdict="MATCH", rule_id="standard_exact_match", variant_axis=variant_axis)
        elif _are_standards_equivalent(str_a, str_b):
            return AttributeVerdict(key=key, tier=tier, a_value=val_a, b_value=val_b, verdict="COMPATIBLE", rule_id="standard_equiv_compatible", variant_axis=variant_axis)
        else:
            return AttributeVerdict(key=key, tier=tier, a_value=val_a, b_value=val_b, verdict="CONFLICT", rule_id="standard_conflict", variant_axis=variant_axis)

    elif comparator == "SIZE_TABLE":
        od_a = _parse_pipe_size(val_a)
        od_b = _parse_pipe_size(val_b)
        if od_a is not None and od_b is not None:
            if abs(od_a - od_b) < 0.1:
                return AttributeVerdict(key=key, tier=tier, a_value=val_a, b_value=val_b, verdict="MATCH", rule_id="size_table_match", variant_axis=variant_axis)
            else:
                return AttributeVerdict(key=key, tier=tier, a_value=val_a, b_value=val_b, verdict="CONFLICT", rule_id="size_table_conflict", variant_axis=variant_axis)
        if str(val_a).strip().upper() == str(val_b).strip().upper():
            return AttributeVerdict(key=key, tier=tier, a_value=val_a, b_value=val_b, verdict="MATCH", rule_id="size_str_match", variant_axis=variant_axis)
        return AttributeVerdict(key=key, tier=tier, a_value=val_a, b_value=val_b, verdict="CONFLICT", rule_id="size_conflict", variant_axis=variant_axis)

    # Fallback default comparison
    if str(val_a).strip().upper() == str(val_b).strip().upper():
        return AttributeVerdict(key=key, tier=tier, a_value=val_a, b_value=val_b, verdict="MATCH", rule_id="fallback_match", variant_axis=variant_axis)
    return AttributeVerdict(key=key, tier=tier, a_value=val_a, b_value=val_b, verdict="CONFLICT", rule_id="fallback_conflict", variant_axis=variant_axis)

def compare_attribute_lists(
    attrs_a: list[dict],
    attrs_b: list[dict],
    pack_config: dict
) -> list[AttributeVerdict]:
    map_a = {a.get("key"): a for a in attrs_a if isinstance(a, dict) and a.get("key")}
    map_b = {b.get("key"): b for b in attrs_b if isinstance(b, dict) and b.get("key")}

    verdicts: list[AttributeVerdict] = []
    pack_attrs = pack_config.get("attributes", [])

    for attr_def in pack_attrs:
        key = attr_def.get("key")
        if not key:
            continue
        a_val = map_a.get(key)
        b_val = map_b.get(key)
        verdict = compare_single_attribute(key, attr_def, a_val, b_val)
        verdicts.append(verdict)

    return verdicts
