import re
from typing import Dict, List, Optional, Any, Tuple

MATERIAL_TYPES: List[Tuple[str, str]] = [
    ("BALL VALVE", "ball valve"),
    ("GATE VALVE", "gate valve"),
    ("CHECK VALVE", "check valve"),
    ("GLOBE VALVE", "globe valve"),
    ("BUTTERFLY VALVE", "butterfly valve"),
    ("CONTROL VALVE", "control valve"),
    ("VALVE", "valve"),
    ("CENTRIFUGAL PUMP", "centrifugal pump"),
    ("RECIPROCATING COMPRESSOR", "reciprocating compressor"),
    ("AIR COMPRESSOR", "air compressor"),
    ("COMPRESSOR", "compressor"),
    ("PUMP", "pump"),
    ("TRANSFORMER", "transformer"),
    ("CYLINDER", "cylinder"),
    ("ROTARY EVAPORATOR", "rotary evaporator"),
    ("EVAPORATION SYSTEM", "evaporation system"),
    ("EVAPORATOR", "evaporator"),
    ("HEX BOLT", "bolt"),
    ("HEXAGONAL BOLT", "bolt"),
    ("STUD BOLT", "stud bolt"),
    ("ANCHOR BOLT", "anchor bolt"),
    ("BOLT", "bolt"),
    ("BALL BEARING", "ball bearing"),
    ("ROLLER BEARING", "roller bearing"),
    ("BEARING", "bearing"),
    ("SEAMLESS PIPE", "seamless pipe"),
    ("ERW PIPE", "erw pipe"),
    ("PIPE", "pipe"),
    ("GASKET", "gasket"),
    ("CABLE", "cable"),
    ("FLANGE", "flange"),
    ("NUT", "nut"),
    ("WASHER", "washer"),
]

CONNECTION_TYPES: List[Tuple[str, str]] = [
    ("FLANGED", "flanged"),
    ("THREADED", "threaded"),
    ("SOCKET WELD", "socket weld"),
    ("SW", "socket weld"),
    ("BUTT WELD", "butt weld"),
    ("BW", "butt weld"),
    ("WAFER", "wafer"),
    ("LUG", "lug"),
    ("NPT", "npt threaded"),
]

# Recognized Engineering Units for Measurements
ENGINEERING_UNITS_REGEX = r'(?:M3/HR|M3/H|LPM|SQMM|DEG\s*C|°C|BAR|PSI|KG|MG|ML|MM|CM|FT|IN|KV|KW|HP|HZ|RPM|L|M|V|A|F|NB)'

# Unit normalization map
UNIT_NORM_MAP = {
    "DEG C": "°C",
    "DEGC": "°C",
    "M3/H": "M3/HR",
}

MEASUREMENT_REGEX = re.compile(
    r'\b(\d+(?:\.\d+)?)\s*(' + ENGINEERING_UNITS_REGEX + r')\b',
    re.IGNORECASE
)

STANDARDS_PATTERNS = [
    r'\b(API\s*\d+[A-Z]?)\b',
    r'\b(ASME(?:\s+[A-Z0-9\.]+)?)\b',
    r'\b(ASTM(?:\s+[A-Z0-9\.]+)?)\b',
    r'\b(IEC\s*\d+)\b',
    r'\b(DIN\s*\d+)\b',
    r'\b(ISO\s*\d+)\b',
    r'\b(BS\s*\d+)\b',
    r'\b(IS\s*\d+)\b',
]


def extract_measurements(upper_text: str) -> List[Dict[str, Any]]:
    """
    Extracts structured measurements (numeric value + engineering unit).
    Excludes standalone numbers without recognized engineering units.
    """
    measurements: List[Dict[str, Any]] = []
    seen = set()

    for match in MEASUREMENT_REGEX.finditer(upper_text):
        val_str, unit_raw = match.groups()
        try:
            val = float(val_str)
        except ValueError:
            continue

        unit_norm = unit_raw.upper().strip()
        if unit_norm in UNIT_NORM_MAP:
            unit_norm = UNIT_NORM_MAP[unit_norm]

        key = (val, unit_norm)
        if key not in seen:
            seen.add(key)
            measurements.append({
                "value": val,
                "unit": unit_norm
            })

    return measurements


def extract_standards(upper_text: str) -> List[str]:
    """
    Extracts technical standards and specifications (e.g. API 610, API 6D, ASME B16.5).
    """
    standards: List[str] = []
    seen = set()

    for pattern in STANDARDS_PATTERNS:
        for match in re.finditer(pattern, upper_text):
            std = match.group(1).strip()
            # Clean up spacing (e.g. API 610, API 6D)
            std_clean = re.sub(r'\s+', ' ', std)
            if std_clean not in seen:
                seen.add(std_clean)
                standards.append(std_clean)

    return standards


def extract_attributes(text: str) -> Dict[str, Any]:
    """
    Deterministically extracts engineering attributes from a material description string.
    Uses rules and regular expressions (CPU-efficient, zero LLM dependency).
    """
    if not text:
        return {}

    attributes: Dict[str, Any] = {}
    upper_text = text.upper()

    # 1. Material Type & Product Type
    for pattern, val in MATERIAL_TYPES:
        if re.search(r'\b' + pattern + r'\b', upper_text):
            attributes["material_type"] = val
            attributes["product_type"] = pattern
            break

    # 2. Connection Type
    for pattern, val in CONNECTION_TYPES:
        if re.search(r'\b' + pattern + r'\b', upper_text):
            attributes["connection_type"] = val
            break

    # 3. Diameter / Thread Size (e.g. M16, M12, DN50, 1/2 INCH)
    diameter_match = re.search(r'\b(M\d+|DN\d+)\b', upper_text)
    if diameter_match:
        attributes["diameter"] = diameter_match.group(1)

    # 4. Metric Bolt Dimensions (e.g. M16 X 70 -> diameter: M16, length: 70)
    m_dim_match = re.search(r'\b(M\d+)\s*[X]\s*(\d+)\b', upper_text)
    if m_dim_match:
        attributes["diameter"] = m_dim_match.group(1)
        attributes["length"] = m_dim_match.group(2)

    # 5. Size (e.g. 1 INCH, 1/2", 50 MM)
    size_match = re.search(r'\b(\d+(?:/\d+)?(?:\.\d+)?\s*(?:INCH|IN|\"|MM))\b', upper_text)
    if size_match:
        attributes["size"] = size_match.group(1).lower()

    # 6. Pressure Class (e.g. CLASS 300, 300 LB, #300, PN16)
    class_match = re.search(r'\b(?:CLASS|CL|#)\s*([0-9]+)\b', upper_text)
    if class_match:
        attributes["pressure_class"] = class_match.group(1)
    else:
        lb_match = re.search(r'\b([0-9]+)\s*(?:LB|LBS|PN)\b', upper_text)
        if lb_match:
            attributes["pressure_class"] = lb_match.group(1)

    # 7. Schedule (e.g. SCH 40, SCH 80, SCH 160, SCH XS)
    sch_match = re.search(r'\bSCH(?:EDULE)?\s*([0-9A-Z]+)\b', upper_text)
    if sch_match:
        attributes["schedule"] = sch_match.group(1)

    # 8. Grade / Strength Class (e.g. GRADE 10.9, GR 8.8, B7, 316L, C3)
    grade_match = re.search(r'\bGRADE\s*([0-9\.]+)\b', upper_text)
    if grade_match:
        attributes["grade"] = grade_match.group(1)
    else:
        gr_match = re.search(r'\bGR\s*([0-9A-Z\.]+)\b', upper_text)
        if gr_match:
            attributes["grade"] = gr_match.group(1)
        else:
            std_grade = re.search(r'\b(B7|B8|B8M|C3|8\.8|10\.9|12\.9)\b', upper_text)
            if std_grade:
                attributes["grade"] = std_grade.group(1)

    # 9. Material / Metallurgy (e.g. SS316, SS304, SS316L, CS, STAINLESS STEEL, CARBON STEEL)
    mat_match = re.search(r'\b(SS\s*316L?|SS\s*304L?|SS\s*410|SS316|SS304|SS316L|SS410|STAINLESS STEEL|CARBON STEEL|BRASS|COPPER|BRONZE)\b', upper_text)
    if mat_match:
        attributes["material"] = mat_match.group(1).replace(" ", "")

    # 10. Technical Standards
    standards = extract_standards(upper_text)
    if standards:
        attributes["standards"] = standards
        if "specification_standard" not in attributes:
            attributes["specification_standard"] = standards[0]

    # Specification Standard fallback
    if "specification_standard" not in attributes:
        spec_match = re.search(r'\b(ASTM\s+[A-Z0-9]+|DIN\s+[0-9]+|ISO\s+[0-9]+|BS\s+[0-9]+|IS\s+[0-9]+)\b', upper_text)
        if spec_match:
            attributes["specification_standard"] = spec_match.group(1)

    # 11. Unit of Measure (UOM)
    uom_match = re.search(r'\b(MM|INCH|MTR|KG|NOS|PCS|SET)\b', upper_text)
    if uom_match:
        attributes["uom"] = uom_match.group(1)

    # 12. Structured Measurements (Numeric Value + Unit)
    measurements = extract_measurements(upper_text)
    attributes["measurements"] = measurements

    return attributes
