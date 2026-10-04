import re
import unicodedata
from dataclasses import dataclass, field
from app.config_loader.loader import load_config_bundle

@dataclass
class NormalizedText:
    text: str
    tokens: list[str] = field(default_factory=list)
    applied_rules: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)

def normalize_text(raw_text: str | None) -> NormalizedText:
    """
    Applies ordered, deterministic text normalization steps as specified in ARCHITECT.md §13.
    """
    if not raw_text or not str(raw_text).strip():
        return NormalizedText(text="", tokens=[], applied_rules=["empty_input"], flags=["empty_description"])

    applied_rules = []
    flags = []
    
    # 1. Unicode NFKC normalization
    s = unicodedata.normalize("NFKC", str(raw_text))
    applied_rules.append("nfkc")
    
    # Check non-printable / control chars
    if any(unicodedata.category(c).startswith("C") for c in s):
        s = "".join(c for c in s if not unicodedata.category(c).startswith("C"))
        flags.append("control_characters_stripped")
        applied_rules.append("strip_control_chars")

    # Flag CSV injection risk
    if raw_text.strip().startswith(("=", "+", "-", "@")):
        flags.append("csv_injection_risk")

    # Replace diameter symbols Ø, Φ, ϕ with DIA
    if re.search(r"[ØΦϕ]", s):
        s = re.sub(r"[ØΦϕ]", " DIA ", s)
        applied_rules.append("symbol_dia")

    # Replace multiplication symbols × or * between numbers with x
    s = re.sub(r"(?<=\d)\s*[×*]\s*(?=\d)", "X", s)
    applied_rules.append("multiplication_x")

    # Normalise quotes following number: 4" -> 4 IN
    s = re.sub(r"(?<=\d)\s*[\"″”]\b", " IN ", s)
    s = re.sub(r"(?<=\d)\s*[\"″”]", " IN ", s)
    applied_rules.append("inch_quotes")

    # 2. Uppercase & collapse whitespace
    s = s.upper()
    s = re.sub(r"\s+", " ", s).strip()
    applied_rules.append("uppercase_and_collapse_ws")

    # 4. Split glued size/grade/standard tokens
    # e.g., M10X50 -> M10 X 50
    s = re.sub(r"\b(M\d{1,3})X(\d{1,3})\b", r"\1 X \2", s)
    # e.g., GR8.8 -> GR 8.8
    s = re.sub(r"\bGR(\d{1,2}\.\d)\b", r"GR \1", s)
    # e.g., IS1363 -> IS 1363
    s = re.sub(r"\b(IS|DIN|ISO|ASME|ASTM)(\d{3,5})\b", r"\1 \2", s)
    # e.g., SS304 -> SS 304, SS316 -> SS 316
    s = re.sub(r"\b(SS|CS|AS)(\d{3})\b", r"\1 \2", s)
    applied_rules.append("unglue_tokens")

    # Truncate length warning if > 500 chars
    if len(s) > 500:
        s = s[:500]
        flags.append("description_truncated_500")

    # 5. Expand abbreviations from abbreviations.yaml
    bundle = load_config_bundle()
    abbrev_dict = bundle.abbreviations
    if not isinstance(abbrev_dict, dict):
        abbrev_dict = {}

    tokens_raw = re.split(r"[\s,;]+", s)
    expanded_tokens = []
    
    for tok in tokens_raw:
        if not tok:
            continue
        # Clean token punctuation for lookup, e.g., 'SS,' -> 'SS'
        clean_tok = tok.strip(".,;")
        if clean_tok in abbrev_dict:
            expanded_tokens.append(abbrev_dict[clean_tok])
        else:
            expanded_tokens.append(tok)
            
    applied_rules.append("abbreviation_expansion")
    
    normalized_str = " ".join(expanded_tokens)
    final_tokens = [t for t in re.split(r"[\s,;]+", normalized_str) if t]
    
    return NormalizedText(
        text=normalized_str,
        tokens=final_tokens,
        applied_rules=applied_rules,
        flags=flags
    )
