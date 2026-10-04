import re
from app.config_loader.loader import load_config_bundle

def normalize_uom(raw_uom: str | None) -> tuple[str | None, str | None, list[str]]:
    """
    Normalizes a raw UOM string to (uom_canonical, uom_dimension, flags).
    Returns (None, None, ['unknown_uom']) if unmapped or unknown.
    """
    if not raw_uom or not str(raw_uom).strip():
        return None, None, ["uom_missing"]
    
    clean_uom = str(raw_uom).strip().upper()
    # Remove punctuation/trailing dots e.g., 'NOS.' -> 'NOS'
    clean_uom = re.sub(r"[^\w]", "", clean_uom)
    
    bundle = load_config_bundle()
    uom_table = bundle.uom.get("units", bundle.uom) if isinstance(bundle.uom, dict) else {}
    
    if clean_uom in uom_table:
        info = uom_table[clean_uom]
        if isinstance(info, dict):
            return info.get("canonical"), info.get("dimension"), []
        return str(info), "UNKNOWN", []
        
    # Check common aliases
    alias_map = {
        "NOS": ("EA", "COUNT"), "NO": ("EA", "COUNT"), "NUMBERS": ("EA", "COUNT"),
        "PCS": ("EA", "COUNT"), "PC": ("EA", "COUNT"), "PIECE": ("EA", "COUNT"),
        "MTR": ("M", "LENGTH"), "METER": ("M", "LENGTH"), "METERS": ("M", "LENGTH"),
        "KGS": ("KG", "MASS"), "KILOGRAM": ("KG", "MASS"), "KILOGRAMS": ("KG", "MASS"),
        "LTR": ("L", "VOLUME"), "LITER": ("L", "VOLUME"), "LITERS": ("L", "VOLUME")
    }
    if clean_uom in alias_map:
        canon, dim = alias_map[clean_uom]
        return canon, dim, []
        
    return None, None, ["unknown_uom"]
