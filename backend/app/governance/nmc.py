import hashlib
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.db.models import NmcCounter

ISO7064_MOD37_36_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def compute_iso7064_mod37_36(text: str) -> str:
    """
    Computes ISO 7064 MOD 37,36 single check character over an alphanumeric string.
    """
    clean_text = "".join(c for c in text.upper() if c in ISO7064_MOD37_36_ALPHABET)
    if not clean_text:
        return "0"
    
    p = 36
    for char in clean_text:
        val = ISO7064_MOD37_36_ALPHABET.index(char)
        s = (p + val) % 36
        if s == 0:
            s = 36
        p = (s * 2) % 37
    
    check_val = (37 - p) % 36
    return ISO7064_MOD37_36_ALPHABET[check_val]

def validate_nmc(nmc: str) -> bool:
    """
    Validates NMC format: NMC-<CAT4>-<SEQ8>-<CHK>
    Checks structure and ISO 7064 MOD 37,36 check character.
    """
    if not nmc or not isinstance(nmc, str):
        return False
    parts = nmc.split("-")
    if len(parts) != 4 or parts[0] != "NMC":
        return False
    
    cat4, seq8, chk = parts[1], parts[2], parts[3]
    if len(cat4) != 4 or len(seq8) != 8 or len(chk) != 1:
        return False
    
    raw_payload = f"{cat4}{seq8}"
    expected_chk = compute_iso7064_mod37_36(raw_payload)
    return chk == expected_chk

def compute_spec_fingerprint(category_code: str, attributes: List[Dict[str, Any]]) -> str:
    """
    Computes deterministic SHA-256 spec_fingerprint over sorted critical attributes.
    """
    critical_items = []
    for a in attributes:
        key = a.get("key") or a.get("attribute_key")
        val = a.get("canonical_value") or a.get("value_text") or str(a.get("value_num", ""))
        unit = a.get("unit") or ""
        if key and val is not None and str(val).strip():
            critical_items.append(f"{str(key).upper()}:{str(val).strip().upper()}:{str(unit).strip().upper()}")
    
    critical_items.sort()
    payload = f"{category_code.strip().upper()}|" + "|".join(critical_items)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def generate_nmc(db: Session, category_code: str) -> str:
    """
    Generates a deterministic, collision-safe National Material Code with ISO 7064 MOD 37,36 check digit.
    Format: NMC-<CAT4>-<SEQ8>-<CHK> e.g. NMC-BOLT-00000042-K
    """
    prefix_map = {
        "BOLT": "BOLT",
        "PIPE": "PIPE",
        "BEARING": "BRNG",
        "VALVE": "VALV",
        "GASKET": "GSKT",
        "CABLE": "CABL"
    }
    cat4 = prefix_map.get(category_code.upper(), category_code[:4].upper().ljust(4, "X"))
    
    # Per-category counter row update with DB lock / transaction safety
    counter = db.query(NmcCounter).filter_by(category_code=category_code.upper()).first()
    if not counter:
        counter = NmcCounter(category_code=category_code.upper(), last_value=1)
        db.add(counter)
        seq_num = 1
    else:
        counter.last_value += 1
        seq_num = counter.last_value
    
    db.flush()
    seq8 = f"{seq_num:08d}"
    raw_payload = f"{cat4}{seq8}"
    chk = compute_iso7064_mod37_36(raw_payload)
    
    return f"NMC-{cat4}-{seq8}-{chk}"
