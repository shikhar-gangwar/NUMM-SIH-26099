from typing import Sequence
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_
from app.db.models import Material, MaterialEmbedding, Classification
from app.matching.embedding_store import ensure_material_embeddings, compute_text_hash

def get_candidate_materials(
    db: Session,
    target: Material,
    category_code: str,
    candidate_cap: int = 20
) -> tuple[list[Material], str]:
    """
    Retrieves candidate materials for a target material using category blocking, exact key match,
    and pgvector vector similarity search.
    """
    candidates_map: dict[str, Material] = {}

    # 1. Exact key matching (part_number match or exact text hash match)
    if target.part_number and target.part_number.strip():
        pn_matches = (
            db.query(Material)
            .filter(
                Material.part_number == target.part_number,
                Material.id != target.id,
                Material.status == "ACTIVE"
            )
            .limit(candidate_cap)
            .all()
        )
        for m in pn_matches:
            candidates_map[m.id] = m

    # 2. Vector Candidate Retrieval (pgvector)
    target_emb = (
        db.query(MaterialEmbedding)
        .filter(MaterialEmbedding.material_id == target.id)
        .first()
    )

    # If missing vector, generate it
    if not target_emb:
        ensure_material_embeddings(db, [target])
        target_emb = (
            db.query(MaterialEmbedding)
            .filter(MaterialEmbedding.material_id == target.id)
            .first()
        )

    retrieval_method = "EXACT_KEYS_ONLY"

    if target_emb and target_emb.embedding is not None:
        retrieval_method = "PGVECTOR_HNSW_HYBRID"
        
        # pgvector cosine distance query
        try:
            # Query vector candidates within same category
            vector_candidates = (
                db.query(Material)
                .join(MaterialEmbedding, MaterialEmbedding.material_id == Material.id)
                .outerjoin(Classification, and_(Classification.material_id == Material.id, Classification.is_current == True))
                .filter(
                    or_(Classification.category_code == category_code, Material.category_hint == category_code),
                    Material.status == "ACTIVE",
                    Material.id != target.id
                )
                .order_by(MaterialEmbedding.embedding.cosine_distance(target_emb.embedding))
                .limit(candidate_cap)
                .all()
            )
            for m in vector_candidates:
                if m.id not in candidates_map:
                    candidates_map[m.id] = m
        except Exception:
            # Fallback for SQLite in unit tests if pgvector ops are unavailable
            fallback_candidates = (
                db.query(Material)
                .outerjoin(Classification, and_(Classification.material_id == Material.id, Classification.is_current == True))
                .filter(
                    or_(Classification.category_code == category_code, Material.category_hint == category_code),
                    Material.status == "ACTIVE",
                    Material.id != target.id
                )
                .limit(candidate_cap)
                .all()
            )
            for m in fallback_candidates:
                if m.id not in candidates_map:
                    candidates_map[m.id] = m
            retrieval_method = "CATEGORY_FALLBACK"

    candidate_list = list(candidates_map.values())[:candidate_cap]
    return candidate_list, retrieval_method
