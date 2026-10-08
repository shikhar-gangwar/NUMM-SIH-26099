import re

def normalize_text(text: str) -> str:
    """
    Normalizes raw industrial material descriptions into a consistent representation.
    Preserves all numbers, units, engineering grades, and technical identifiers.
    """
    if not text or not isinstance(text, str):
        return ""

    # Convert to uppercase
    result = text.upper().strip()

    # Replace multiplication / dimension symbols (×, x between numbers/units)
    result = re.sub(r'(\d+)\s*[×X]\s*(\d+)', r'\1 X \2', result)

    # Normalize spaces around dimension/separator characters
    result = re.sub(r'\s+X\s+', ' X ', result)

    # Normalize slashes between words/numbers (e.g., 6308/C3 -> 6308 C3, SCH-40 -> SCH 40)
    result = re.sub(r'(?<=\w)/(?=\w)', ' ', result)

    # Standardize common units and identifiers with spacing (e.g., 70MM -> 70 MM, 1INCH -> 1 INCH)
    result = re.sub(r'(\d+)\s*(MM|CM|M|INCH|IN|KG|BAR|PSI|MPA|G|L|V|W|KW|HP|RPM)\b', r'\1 \2', result)

    # Ensure grade, class, schedule formatting consistency
    result = re.sub(r'\bGR(?:ADE)?\s*([0-9\.]+)\b', r'GRADE \1', result)
    result = re.sub(r'\bCL(?:ASS)?\s*([0-9]+)\b', r'CLASS \1', result)
    result = re.sub(r'\bSCH(?:EDULE)?\s*([0-9]+)\b', r'SCH \1', result)

    # Remove extra special characters while keeping numbers, dots, hyphens, and letters
    result = re.sub(r'[^A-Z0-9\.\-\s]', ' ', result)

    # Collapse multiple whitespaces into a single space
    result = re.sub(r'\s+', ' ', result).strip()

    return result
