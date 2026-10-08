import re

# Dictionary of standalone industrial word abbreviations
INDUSTRIAL_ABBREVIATIONS = {
    "BRG": "BEARING",
    "VLV": "VALVE",
    "FLG": "FLANGE",
    "STR": "STRAINER",
    "PLG": "PLUG",
    "STN": "STAINLESS",
    "GALV": "GALVANIZED",
    "MS": "MILD STEEL",
    "CS": "CARBON STEEL",
    "GI": "GALVANIZED IRON",
    "SS": "STAINLESS STEEL",
    "HT": "HIGH TENSILE",
    "HEX": "HEXAGONAL",
}

def expand_abbreviations(text: str) -> str:
    """
    Expands safe standalone industrial abbreviations while preserving compound technical identifiers.
    For example:
      - 'SS' -> 'STAINLESS STEEL'
      - 'SS316' -> 'SS316' (preserved, NOT expanded to STAINLESS STEEL316)
      - 'BRG' -> 'BEARING'
      - 'VLV' -> 'VALVE'
    """
    if not text:
        return ""

    tokens = text.split()
    expanded_tokens = []

    for token in tokens:
        # If token matches compound tech spec like SS316, SS304, 6308ZZ, M16, ASTM A53, do not expand
        if re.match(r'^(SS|CS|MS|GI|SA|ASTM|DIN|ISO|BS|IS)\d+[A-Z0-9]*$', token):
            expanded_tokens.append(token)
        elif token in INDUSTRIAL_ABBREVIATIONS:
            expanded_tokens.append(INDUSTRIAL_ABBREVIATIONS[token])
        else:
            expanded_tokens.append(token)

    result = " ".join(expanded_tokens)

    # Standardize canonical phrase order for common components
    result = re.sub(r'\bHEXAGONAL\s+BOLT\b', 'BOLT HEXAGONAL', result)
    result = re.sub(r'\bHEX\s+BOLT\b', 'BOLT HEXAGONAL', result)

    return result
