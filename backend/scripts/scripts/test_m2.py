import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.abspath("backend"))

from app.normalization.uom import normalize_uom
from app.normalization.text import normalize_text
from app.extraction.extractor import detect_category, extract_attributes

def test_m2_components():
    print("Testing M2 Ingestion & Normalization Components...")

    # 1. Text & UOM Normalization
    canon, dim, flags = normalize_uom("NOS")
    assert canon == "EA" and dim == "COUNT", "UOM normalization failed"
    print("[OK] UOM Normalization: OK")

    norm = normalize_text("BOLT HEX M10X50 SS304 GR 8.8")
    assert "STAINLESS STEEL" in norm.text, "Abbreviation expansion failed"
    print("[OK] Text Normalization: OK")

    # 2. Category Detection & Attribute Extraction (6 categories)
    categories = {
        "HEXAGON HEAD BOLT M10X50 SS304": "BOLT",
        "PIPE 4 INCH SCH 40 SEAMLESS": "PIPE",
        "BEARING 6205 2RS C3": "BEARING",
        "GATE VALVE 2 INCH CLASS 150": "VALVE",
        "SPIRAL WOUND GASKET 4 INCH": "GASKET",
        "CABLE 4C X 16 SQMM COPPER": "CABLE"
    }

    for text, expected in categories.items():
        detected = detect_category(text)
        assert detected == expected, f"Category detection failed for {text}: expected {expected}, got {detected}"
        attrs = extract_attributes(text, detected)
        assert len(attrs) > 0, f"Extraction failed for category {expected}"
        print(f"[OK] Category '{expected}' detection & extraction: OK ({len(attrs)} attrs)")

    print("\nALL M2 VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_m2_components()
