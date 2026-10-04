import re
from dataclasses import dataclass, field
from app.config_loader.loader import load_config_bundle

@dataclass
class ExtractedAttribute:
    key: str
    raw_text: str | None = None
    value_text: str | None = None
    value_num: float | None = None
    unit: str | None = None
    canonical_value: str | None = None
    source: str = "RULE"  # STRUCTURED, RULE, LLM, REVIEWER
    confidence: float = 1.0
    assumed: bool = False
    internal_conflict: bool = False
    span: list[int] | None = None
    rule_id: str | None = None

def detect_category(text: str, hint: str | None = None) -> str:
    """
    Detects one of the 6 P0 category codes (BOLT, PIPE, BEARING, VALVE, GASKET, CABLE) or returns UNCLASSIFIED.
    """
    clean_hint = (hint or "").upper()
    if "BOLT" in clean_hint or "FASTENER" in clean_hint:
        return "BOLT"
    if "PIPE" in clean_hint or "TUBE" in clean_hint:
        return "PIPE"
    if "BEARING" in clean_hint or "BRG" in clean_hint:
        return "BEARING"
    if "VALVE" in clean_hint or "VLV" in clean_hint:
        return "VALVE"
    if "GASKET" in clean_hint or "GSKT" in clean_hint:
        return "GASKET"
    if "CABLE" in clean_hint or "WIRE" in clean_hint or "CBL" in clean_hint:
        return "CABLE"

    clean_text = text.upper()
    bundle = load_config_bundle()
    
    # Check category pack classifier keywords
    for code, pack in bundle.category_packs.items():
        keywords = pack.get("classifier_keywords", [])
        for kw in keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", clean_text):
                return code
                
    # Direct token keyword matching
    if any(k in clean_text for k in ["FASTENER", "STUD", "CAP SCREW", "HEX BOLT", "M10", "M12", "M16", "M20"]):
        return "BOLT"
    if any(k in clean_text for k in ["SCH 40", "SCH 80", "SEAMLESS PIPE", "ERW PIPE", "API 5L", "A106"]):
        return "PIPE"
    if any(k in clean_text for k in ["BALL BEARING", "DEEP GROOVE", "6205", "6308", "2RS"]):
        return "BEARING"
    if any(k in clean_text for k in ["GATE VALVE", "GLOBE VALVE", "CHECK VALVE", "BALL VALVE", "BUTTERFLY VALVE"]):
        return "VALVE"
    if any(k in clean_text for k in ["SPIRAL WOUND", "FLAT RING", "RTJ GASKET"]):
        return "GASKET"
    if any(k in clean_text for k in ["SQMM", "CORE", "ARMOURED", "XLPE", "1.1KV"]):
        return "CABLE"

    return "UNCLASSIFIED"

def extract_attributes(
    normalized_text: str,
    category_code: str,
    manufacturer: str | None = None,
    part_number: str | None = None
) -> list[ExtractedAttribute]:
    """
    Extracts category-pack-driven attributes for a given category code.
    """
    attrs: list[ExtractedAttribute] = []
    
    # 1. Structured attributes
    if manufacturer and manufacturer.strip():
        attrs.append(ExtractedAttribute(
            key="manufacturer",
            raw_text=manufacturer.strip(),
            value_text=manufacturer.strip().upper(),
            canonical_value=manufacturer.strip().upper(),
            source="STRUCTURED",
            confidence=1.0,
            rule_id="struct_manufacturer"
        ))
    if part_number and part_number.strip():
        attrs.append(ExtractedAttribute(
            key="part_number",
            raw_text=part_number.strip(),
            value_text=part_number.strip().upper(),
            canonical_value=part_number.strip().upper(),
            source="STRUCTURED",
            confidence=1.0,
            rule_id="struct_part_number"
        ))
        
    text = normalized_text.upper()
    
    if category_code == "BOLT":
        # Fastener type
        m_type = re.search(r"\b(STUD|STUD BOLT|CAP SCREW|SET SCREW|ANCHOR BOLT|U BOLT|HEX BOLT|HEXAGON BOLT|HEXAGON HEAD BOLT|HEX HEAD BOLT|BOLT HEX|BOLT HEXAGON)\b", text)
        if m_type:
            val = m_type.group(1).replace(" ", "_")
            if "HEX" in val: val = "HEX_BOLT"
            elif "STUD" in val: val = "STUD_BOLT"
            attrs.append(ExtractedAttribute(key="fastener_type", raw_text=m_type.group(0), value_text=val, canonical_value=val, rule_id="bolt_type"))
        elif "HEX" in text or "HEXAGON" in text:
            attrs.append(ExtractedAttribute(key="fastener_type", raw_text="HEX", value_text="HEX_BOLT", canonical_value="HEX_BOLT", rule_id="bolt_type_hex"))
        else:
            attrs.append(ExtractedAttribute(key="fastener_type", raw_text="BOLT", value_text="HEX_BOLT", canonical_value="HEX_BOLT", assumed=True, rule_id="bolt_type_assumed"))
            
        # Nominal diameter & length (e.g. M10 X 50)
        m_dim = re.search(r"\bM\s?(?P<d>\d{1,2}(\.\d)?)\s*X\s*(?P<l>\d{2,3})\b", text)
        if m_dim:
            d_val = float(m_dim.group("d"))
            l_val = float(m_dim.group("l"))
            attrs.append(ExtractedAttribute(key="nominal_diameter", raw_text=m_dim.group("d"), value_num=d_val, unit="mm", canonical_value=f"M{m_dim.group('d')}", rule_id="bolt_dia"))
            attrs.append(ExtractedAttribute(key="length", raw_text=m_dim.group("l"), value_num=l_val, unit="mm", canonical_value=f"{l_val}mm", rule_id="bolt_len"))
        else:
            # Separate size extraction
            m_dia = re.search(r"\bM\s?(?P<d>\d{1,2})\b", text)
            if m_dia:
                d_val = float(m_dia.group("d"))
                attrs.append(ExtractedAttribute(key="nominal_diameter", raw_text=m_dia.group("d"), value_num=d_val, unit="mm", canonical_value=f"M{m_dia.group('d')}", rule_id="bolt_dia_single"))
                
        # Property class (e.g., 4.6, 8.8, 10.9, 12.9, A2-70, A4-80)
        m_prop = re.search(r"\b(A[24]-(?:50|70|80)|4\.6|4\.8|5\.6|5\.8|6\.8|8\.8|9\.8|10\.9|12\.9)\b", text)
        if m_prop:
            attrs.append(ExtractedAttribute(key="property_class", raw_text=m_prop.group(1), value_text=m_prop.group(1), canonical_value=m_prop.group(1), rule_id="bolt_prop_class"))
            
        # Material (SS304, SS316, STAINLESS STEEL, CARBON STEEL)
        m_mat = re.search(r"\b(STAINLESS STEEL|CARBON STEEL|ALLOY STEEL|SS\s?304|SS\s?316|SS304|SS316|CS|MS)\b", text)
        if m_mat:
            val = m_mat.group(1).replace(" ", "_")
            if "304" in val: val = "SS304"
            elif "316" in val: val = "SS316"
            attrs.append(ExtractedAttribute(key="material", raw_text=m_mat.group(0), value_text=val, canonical_value=val, rule_id="bolt_material"))

        # Standard (IS 1363, DIN 931, ISO 4014)
        m_std = re.search(r"\b(IS|DIN|ISO|ASME|ASTM)\s?[:\-]?\s?(\d{3,5})\b", text)
        if m_std:
            std_str = f"{m_std.group(1)} {m_std.group(2)}"
            attrs.append(ExtractedAttribute(key="standard", raw_text=m_std.group(0), value_text=std_str, canonical_value=std_str, rule_id="bolt_standard"))

    elif category_code == "PIPE":
        # Spec Grade
        m_spec = re.search(r"\b(A106\s*(?:GR\s*B)?|A53\s*(?:GR\s*B)?|API\s*5L\s*(?:X\d{2})?|SS\s?304|SS\s?316)\b", text)
        if m_spec:
            val = m_spec.group(1).replace(" ", "_")
            attrs.append(ExtractedAttribute(key="spec_grade", raw_text=m_spec.group(0), value_text=val, canonical_value=val, rule_id="pipe_spec"))

        # Nominal size (2 IN, 4 IN, DN100, 2", 4")
        m_size = re.search(r"\b(\d{1,2}(?:\.\d)?)\s*(?:IN|INCH|\"|DN\s*(\d{2,3}))\b", text)
        if m_size:
            sz_str = m_size.group(0)
            attrs.append(ExtractedAttribute(key="nominal_size", raw_text=sz_str, value_text=sz_str, canonical_value=sz_str, rule_id="pipe_size"))

        # Schedule or thickness (SCH 40, SCH 80, SCH 160, SCH XS, SCH XXS)
        m_sch = re.search(r"\b(SCH(?:EDULE)?\s*(?:40|80|160|XS|XXS|STD))\b", text)
        if m_sch:
            sch_val = m_sch.group(1).replace("SCHEDULE", "SCH")
            attrs.append(ExtractedAttribute(key="schedule_or_thickness", raw_text=m_sch.group(0), value_text=sch_val, canonical_value=sch_val, rule_id="pipe_sch"))

        # Manufacturing (SEAMLESS, ERW, EFW, WELDED)
        m_mfg = re.search(r"\b(SEAMLESS|ERW|EFW|WELDED)\b", text)
        if m_mfg:
            attrs.append(ExtractedAttribute(key="manufacturing", raw_text=m_mfg.group(1), value_text=m_mfg.group(1), canonical_value=m_mfg.group(1), rule_id="pipe_mfg"))

        # Material (Carbon Steel vs Stainless Steel)
        m_mat = re.search(r"\b(STAINLESS STEEL|CARBON STEEL|ALLOY STEEL|SS\s?304|SS\s?316|SS304|SS316|CS|MS)\b", text)
        if m_mat:
            val = "STAINLESS_STEEL" if ("SS" in m_mat.group(1) or "STAINLESS" in m_mat.group(1)) else "CARBON_STEEL"
            attrs.append(ExtractedAttribute(key="material", raw_text=m_mat.group(0), value_text=val, canonical_value=val, rule_id="pipe_material"))
        elif m_spec:
            spec_str = m_spec.group(0)
            val = "STAINLESS_STEEL" if ("304" in spec_str or "316" in spec_str) else "CARBON_STEEL"
            attrs.append(ExtractedAttribute(key="material", raw_text=spec_str, value_text=val, canonical_value=val, assumed=True, rule_id="pipe_material_inferred"))

    elif category_code == "BEARING":
        # Designation base (e.g. 6205, 6308, 30205)
        m_des = re.search(r"\b(\d{4,5}(?:-[2ZRS]{1,4})?)\b", text)
        if m_des:
            raw_des = m_des.group(1).split("-")[0]
            attrs.append(ExtractedAttribute(key="designation_base", raw_text=m_des.group(1), value_text=raw_des, canonical_value=raw_des, rule_id="brg_desig"))

        # Seal type (2RS, ZZ, Z, RS, OPEN)
        m_seal = re.search(r"\b(2RS|ZZ|2RSR|Z|RS|OPEN)\b", text)
        if m_seal:
            attrs.append(ExtractedAttribute(key="seal_type", raw_text=m_seal.group(1), value_text=m_seal.group(1), canonical_value=m_seal.group(1), rule_id="brg_seal"))
        else:
            attrs.append(ExtractedAttribute(key="seal_type", raw_text="OPEN", value_text="OPEN", canonical_value="OPEN", assumed=True, rule_id="brg_seal_default"))

        # Clearance (C2, C3, C4, CN)
        m_clr = re.search(r"\b(C[234]|CN)\b", text)
        if m_clr:
            attrs.append(ExtractedAttribute(key="clearance", raw_text=m_clr.group(1), value_text=m_clr.group(1), canonical_value=m_clr.group(1), rule_id="brg_clearance"))

        # Standard ISO bearing dimensions lookup table
        BEARING_DIMENSIONS = {
            "6204": (20.0, 47.0, 14.0),
            "6205": (25.0, 52.0, 15.0),
            "6206": (30.0, 62.0, 16.0),
            "6207": (35.0, 72.0, 17.0),
            "6208": (40.0, 80.0, 18.0),
            "6305": (25.0, 62.0, 17.0),
            "6306": (30.0, 72.0, 19.0),
            "6308": (40.0, 90.0, 23.0),
            "6309": (45.0, 100.0, 25.0),
            "6310": (50.0, 110.0, 27.0),
        }
        b_code = m_des.group(1).split("-")[0] if m_des else ""
        if b_code in BEARING_DIMENSIONS:
            id_val, od_val, w_val = BEARING_DIMENSIONS[b_code]
            attrs.append(ExtractedAttribute(key="bearing_type", raw_text="DEEP_GROOVE_BALL", value_text="DEEP_GROOVE_BALL", canonical_value="DEEP_GROOVE_BALL", rule_id="brg_type_iso"))
            attrs.append(ExtractedAttribute(key="inner_dia", raw_text=str(id_val), value_num=id_val, unit="mm", canonical_value=f"{id_val}mm", rule_id="brg_iso_table"))
            attrs.append(ExtractedAttribute(key="outer_dia", raw_text=str(od_val), value_num=od_val, unit="mm", canonical_value=f"{od_val}mm", rule_id="brg_iso_table"))
            attrs.append(ExtractedAttribute(key="width", raw_text=str(w_val), value_num=w_val, unit="mm", canonical_value=f"{w_val}mm", rule_id="brg_iso_table"))

    elif category_code == "VALVE":
        # Valve type (GATE, GLOBE, CHECK, BALL, BUTTERFLY, PLUG)
        m_vtype = re.search(r"\b(GATE|GLOBE|CHECK|BALL|BUTTERFLY|PLUG)\s*(?:VALVE)?\b", text)
        if m_vtype:
            attrs.append(ExtractedAttribute(key="valve_type", raw_text=m_vtype.group(1), value_text=m_vtype.group(1), canonical_value=m_vtype.group(1), rule_id="vlv_type"))

        # Nominal size (2 IN, 4 IN, DN50, DN100, 2", 4")
        m_vsize = re.search(r"\b(\d{1,2}(?:\.\d)?)\s*(?:IN|INCH|\"|DN\s*(\d{2,3}))\b", text)
        if m_vsize:
            attrs.append(ExtractedAttribute(key="nominal_size", raw_text=m_vsize.group(0), value_text=m_vsize.group(0), canonical_value=m_vsize.group(0), rule_id="vlv_size"))

        # Pressure class (150, 300, 600, 900, 1500, 2500)
        m_cls = re.search(r"\b(?:CLASS|CL|PN)?\s*(150|300|600|900|1500|2500|16|40)\b", text)
        if m_cls:
            c_raw = m_cls.group(1)
            # Map PN16 -> 150, PN40 -> 300 if standard
            c_val = "150" if c_raw == "16" else ("300" if c_raw == "40" else c_raw)
            attrs.append(ExtractedAttribute(key="pressure_class", raw_text=c_raw, value_text=c_val, canonical_value=c_val, rule_id="vlv_class"))

        # Body Material
        m_bmat = re.search(r"\b(WCB|CF8M|CF8|SS316|SS304|CAST IRON|CARBON STEEL|FORGED STEEL|A105|A216|A351)\b", text)
        if m_bmat:
            val = m_bmat.group(1)
            attrs.append(ExtractedAttribute(key="body_material", raw_text=val, value_text=val, canonical_value=val, rule_id="vlv_bmat"))
        elif m_vtype:
            attrs.append(ExtractedAttribute(key="body_material", raw_text="WCB", value_text="WCB", canonical_value="WCB", assumed=True, rule_id="vlv_bmat_default"))

        # End connection (FLANGED, THREADED, SOCKET_WELD, BUTT_WELD)
        m_end = re.search(r"\b(FLANGED|THREADED|SOCKET WELD|BUTT WELD)\b", text)
        if m_end:
            val = m_end.group(1).replace(" ", "_")
            attrs.append(ExtractedAttribute(key="end_connection", raw_text=m_end.group(0), value_text=val, canonical_value=val, rule_id="vlv_end"))

    elif category_code == "GASKET":
        # Gasket type (SPIRAL_WOUND, FLAT_RING, RTJ, FULL_FACE)
        m_gtype = re.search(r"\b(SPIRAL WOUND|FLAT RING|RTJ|FULL FACE|SW)\b", text)
        if m_gtype:
            raw = m_gtype.group(0)
            val = "SPIRAL_WOUND" if raw in ["SPIRAL WOUND", "SW"] else raw.replace(" ", "_")
            attrs.append(ExtractedAttribute(key="gasket_type", raw_text=raw, value_text=val, canonical_value=val, rule_id="gskt_type"))

        # Nominal size (2 IN, 4 IN, DN100)
        m_gsize = re.search(r"\b(\d{1,2}(?:\.\d)?)\s*(?:IN|INCH|\"|DN\s*(\d{2,3}))\b", text)
        if m_gsize:
            attrs.append(ExtractedAttribute(key="nominal_size", raw_text=m_gsize.group(0), value_text=m_gsize.group(0), canonical_value=m_gsize.group(0), rule_id="gskt_size"))

        # Pressure class (150, 300, 600, 900, 1500)
        m_cls = re.search(r"\b(?:CLASS|CL|PN)?\s*(150|300|600|900|1500|16|20|40)\b", text)
        if m_cls:
            c_raw = m_cls.group(1)
            c_val = "150" if c_raw in ["16", "20"] else ("300" if c_raw == "40" else c_raw)
            attrs.append(ExtractedAttribute(key="pressure_class", raw_text=c_raw, value_text=c_val, canonical_value=c_val, rule_id="gskt_class"))

        # Material
        m_gmat = re.search(r"\b(SS316|SS304|GRAPHITE|PTFE|CAF|EPDM|NEOPRENE)\b", text)
        if m_gmat:
            attrs.append(ExtractedAttribute(key="material", raw_text=m_gmat.group(1), value_text=m_gmat.group(1), canonical_value=m_gmat.group(1), rule_id="gskt_mat"))
        elif m_gtype and "SPIRAL" in m_gtype.group(0):
            attrs.append(ExtractedAttribute(key="material", raw_text="SS316/GRAPHITE", value_text="SS316_GRAPHITE", canonical_value="SS316_GRAPHITE", assumed=True, rule_id="gskt_mat_default"))

    elif category_code == "CABLE":
        # Conductor material (COPPER, ALUMINIUM)
        m_cond = re.search(r"\b(COPPER|ALUMINIUM|ALUMINUM|CU|AL)\b", text)
        if m_cond:
            raw = m_cond.group(1)
            val = "COPPER" if raw in ["COPPER", "CU"] else "ALUMINIUM"
            attrs.append(ExtractedAttribute(key="conductor_material", raw_text=raw, value_text=val, canonical_value=val, rule_id="cbl_conductor"))

        # Voltage grade (1.1KV, 3.3KV, 6.6KV, 11KV, 33KV)
        m_volt = re.search(r"\b(1\.1\s*KV|3\.3\s*KV|6\.6\s*KV|11\s*KV|33\s*KV|1100\s*V)\b", text)
        if m_volt:
            val = m_volt.group(1).replace(" ", "")
            if val == "1100V": val = "1.1KV"
            attrs.append(ExtractedAttribute(key="voltage_grade", raw_text=m_volt.group(0), value_text=val, canonical_value=val, rule_id="cbl_voltage"))

        # Cores & Cross section (e.g. 3.5C X 95 SQMM, 4C X 16 SQMM)
        m_core = re.search(r"\b(?P<c>\d(?:\.5)?)\s*C(?:ORE)?\s*(?:X|\*)\s*(?P<s>\d{1,3}(?:\.\d)?)\s*(?:SQMM|MM2|SQ\.\s*MM)?\b", text)
        if m_core:
            c_val = float(m_core.group("c"))
            s_val = float(m_core.group("s"))
            attrs.append(ExtractedAttribute(key="cores", raw_text=m_core.group("c"), value_num=c_val, canonical_value=str(m_core.group('c')), rule_id="cbl_cores"))
            attrs.append(ExtractedAttribute(key="cross_section", raw_text=m_core.group("s"), value_num=s_val, unit="mm2", canonical_value=f"{s_val}mm2", rule_id="cbl_sqmm"))

        # Insulation (PVC, XLPE)
        m_ins = re.search(r"\b(PVC|XLPE)\b", text)
        if m_ins:
            attrs.append(ExtractedAttribute(key="insulation", raw_text=m_ins.group(1), value_text=m_ins.group(1), canonical_value=m_ins.group(1), rule_id="cbl_insulation"))

        # Armoured (ARMOURED, UNARMOURED)
        m_arm = re.search(r"\b(UNARMOURED|ARMOURED)\b", text)
        if m_arm:
            attrs.append(ExtractedAttribute(key="armoured", raw_text=m_arm.group(1), value_text=m_arm.group(1), canonical_value=m_arm.group(1), rule_id="cbl_armoured"))

    return attrs
