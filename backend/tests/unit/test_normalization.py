from app.normalization.uom import normalize_uom
from app.normalization.text import normalize_text

def test_uom_normalization_valid():
    canon, dim, flags = normalize_uom("NOS")
    assert canon == "EA"
    assert dim == "COUNT"
    assert len(flags) == 0

def test_uom_normalization_length():
    canon, dim, flags = normalize_uom("MTR")
    assert canon == "M"
    assert dim == "LENGTH"

def test_uom_normalization_unknown():
    canon, dim, flags = normalize_uom("UNKNOWN_UNIT_XYZ")
    assert canon is None
    assert "unknown_uom" in flags

def test_text_normalization_abbreviations():
    res = normalize_text("BOLT HEX M10X50 SS304 GR 8.8")
    assert "STAINLESS STEEL" in res.text
    assert "GRADE" in res.text
    assert "HEXAGON" in res.text
    assert "nfkc" in res.applied_rules

def test_text_normalization_symbol_replacements():
    res = normalize_text("PIPE 4\" DIA Ø")
    assert "IN" in res.text
    assert "DIA" in res.text
