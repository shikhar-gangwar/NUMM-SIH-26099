import os
import hashlib
import json
import yaml
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.models import ModelVersion

class ConfigBundle:
    def __init__(self, scoring: dict, abbreviations: dict, material_aliases: dict, standard_equiv: dict, size_tables: dict, uom: dict, category_packs: dict):
        self.scoring = scoring
        self.abbreviations = abbreviations
        self.material_aliases = material_aliases
        self.standard_equiv = standard_equiv
        self.size_tables = size_tables
        self.uom = uom
        self.category_packs = category_packs

def _stringize_keys(obj):
    if isinstance(obj, dict):
        return {str(k): _stringize_keys(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_stringize_keys(i) for i in obj]
    return obj

def compute_canonical_hash(data: dict) -> str:
    clean_data = _stringize_keys(data)
    canonical_json = json.dumps(clean_data, sort_keys=True)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

def load_yaml(file_path: str) -> tuple[dict, str]:
    if not os.path.exists(file_path):
        return {}, ""
    with open(file_path, "r", encoding="utf-8") as f:
        content = yaml.safe_load(f) or {}
    config_hash = compute_canonical_hash(content)
    return content, config_hash

def register_config_version(db: Session, kind: str, name: str, version_tag: str, config_hash: str) -> ModelVersion:
    existing = db.query(ModelVersion).filter_by(kind=kind, config_hash=config_hash).first()
    if existing:
        return existing
    
    mv = ModelVersion(
        kind=kind,
        provider="internal",
        model_id=name,
        model_version=version_tag,
        config_hash=config_hash,
        status="ACTIVE"
    )
    db.add(mv)
    db.commit()
    db.refresh(mv)
    return mv

def load_config_bundle(db: Session | None = None) -> ConfigBundle:
    scoring, scoring_hash = load_yaml(settings.MATCH_CONFIG_PATH)
    abbrev_raw, _ = load_yaml(settings.ABBREVIATIONS_PATH)
    abbrev = abbrev_raw.get("abbreviations", abbrev_raw)
    
    aliases_raw, _ = load_yaml(settings.MATERIAL_ALIASES_PATH)
    aliases = aliases_raw.get("groups", aliases_raw)
    
    std_equiv_raw, _ = load_yaml(settings.STANDARD_EQUIV_PATH)
    std_equiv = std_equiv_raw.get("equivalences", std_equiv_raw)
    
    sizes_raw, _ = load_yaml(settings.SIZE_TABLES_PATH)
    sizes = sizes_raw.get("pipe_sizes", sizes_raw)
    
    uom_raw, _ = load_yaml(settings.UOM_PATH)
    uom = uom_raw.get("units", uom_raw)
    
    category_packs = {}
    packs_dir = settings.CATEGORY_PACKS_DIR
    if os.path.exists(packs_dir):
        for fname in os.listdir(packs_dir):
            if fname.endswith(".yaml") or fname.endswith(".yml"):
                fpath = os.path.join(packs_dir, fname)
                pack_data, pack_hash = load_yaml(fpath)
                code = pack_data.get("code", fname.split(".")[0])
                category_packs[code] = pack_data
                if db:
                    register_config_version(db, "CATEGORY_PACK", f"pack:{code}", str(pack_data.get("version", 1)), pack_hash)
    
    if db and scoring_hash:
        register_config_version(db, "SCORING_CONFIG", "scoring.yaml", str(scoring.get("version", 1)), scoring_hash)
        
    return ConfigBundle(scoring, abbrev, aliases, std_equiv, sizes, uom, category_packs)
