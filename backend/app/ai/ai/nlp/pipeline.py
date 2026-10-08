import hashlib
from typing import Dict, Any
from app.ai.nlp.normalizer import normalize_text
from app.ai.nlp.abbreviation import expand_abbreviations
from app.ai.nlp.attribute_extractor import extract_attributes

class IndustrialNLPPipeline:
    """
    Lightweight, CPU-friendly NLP pipeline for industrial material descriptions.
    Executes normalization, abbreviation resolution, attribute extraction, and text hashing.
    """

    def process(self, raw_description: str) -> Dict[str, Any]:
        if not raw_description or not isinstance(raw_description, str):
            raw_description = ""

        # Step 1: Text normalization
        norm = normalize_text(raw_description)

        # Step 2: Industrial abbreviation resolution
        expanded = expand_abbreviations(norm)

        # Step 3: Technical attribute extraction
        attributes = extract_attributes(expanded)

        # Step 4: Text hash generation for caching
        text_hash = hashlib.sha256(expanded.encode("utf-8")).hexdigest()

        return {
            "raw_description": raw_description,
            "normalized_text": expanded,
            "extracted_attributes": attributes,
            "text_hash": text_hash
        }

# Global singleton instance for easy import
nlp_pipeline = IndustrialNLPPipeline()
