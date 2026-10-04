import hashlib
from typing import Sequence
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models import Material, MaterialEmbedding, ModelVersion
from app.ai.providers.factory import get_embedding_provider, register_provider_fingerprint
from app.core.ids import generate_uuidv7

def compute_text_hash(text: str) -> str:
    return hashlib.sha256(text.strip().upper().encode("utf-8")).hexdigest()

def ensure_material_embeddings(db: Session, materials: Sequence[Material]) -> tuple[int, ModelVersion]:
    """
    Generates and stores embeddings for materials that do not yet have an embedding
    for the active embedding provider model in the database.
    """
    provider = get_embedding_provider(db=db)
    model_version_row = register_provider_fingerprint(db, provider)
    
    if not materials:
        return 0, model_version_row

    # Collect materials missing embeddings for active model_version_row.id
    missing_materials: list[Material] = []
    text_hashes: list[str] = []

    for mat in materials:
        txt = mat.normalized_text or mat.raw_description or ""
        if not txt.strip():
            continue
        thash = compute_text_hash(txt)
        
        existing = db.query(MaterialEmbedding).filter_by(
            material_id=mat.id,
            model_version_id=model_version_row.id
        ).first()

        if not existing:
            missing_materials.append(mat)
            text_hashes.append(thash)

    if not missing_materials:
        return 0, model_version_row

    texts = [m.normalized_text or m.raw_description or "" for m in missing_materials]
    vectors = provider.embed_documents(texts)

    new_embeddings = []
    for mat, thash, vec in zip(missing_materials, text_hashes, vectors):
        emb_row = MaterialEmbedding(
            id=str(generate_uuidv7()),
            material_id=mat.id,
            model_version_id=model_version_row.id,
            text_hash=thash,
            embedding=vec
        )
        new_embeddings.append(emb_row)
        db.add(emb_row)

    db.commit()
    return len(new_embeddings), model_version_row
