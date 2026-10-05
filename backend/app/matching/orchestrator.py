import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Sequence
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.db.models import (
    Material, Cpse, MatchRun, MaterialMatch, MatchEvidence,
    Classification, MaterialAttribute, MaterialEmbedding, ModelVersion
)
from app.normalization.text import normalize_text, NormalizedText
from app.normalization.uom import normalize_uom
from app.extraction.extractor import detect_category, extract_attributes
from app.matching.embedding_store import ensure_material_embeddings
from app.matching.blocking import get_candidate_materials
from app.matching.engine import evaluate_material_pair
from app.ai.providers.factory import get_reranker_provider
from app.config_loader.loader import load_config_bundle
from app.audit.service import AuditService
from app.core.ids import generate_uuidv7

def _build_material_dict(db: Session, material: Material) -> dict:
    """
    Constructs normalized representation dict of a Material DB entity suitable for the matching engine.
    Ensures classification and attributes exist in DB.
    """
    # 1. Normalized text & UOM
    norm_txt = material.normalized_text
    if not norm_txt:
        norm_res = normalize_text(material.raw_description)
        norm_txt = norm_res.text if isinstance(norm_res, NormalizedText) else str(norm_res)
        material.normalized_text = norm_txt
        db.add(material)

    uom_dim = material.uom_dimension
    if not uom_dim:
        canon, dim, flags = normalize_uom(material.raw_uom)
        material.uom_canonical = canon
        material.uom_dimension = dim or "UNKNOWN"
        db.add(material)

    # 2. Category classification
    cls_row = (
        db.query(Classification)
        .filter_by(material_id=material.id, is_current=True)
        .first()
    )
    if not cls_row:
        cat_code = detect_category(norm_txt, material.category_hint)
        input_hash = hashlib.sha256(norm_txt.encode("utf-8")).hexdigest()
        cls_row = Classification(
            id=str(generate_uuidv7()),
            material_id=material.id,
            category_code=cat_code,
            confidence=1.0 if cat_code != "UNCLASSIFIED" else 0.5,
            method="RULE_KEYWORD",
            input_hash=input_hash,
            is_current=True
        )
        db.add(cls_row)

    # 3. Attributes
    attr_rows = (
        db.query(MaterialAttribute)
        .filter_by(material_id=material.id, is_current=True)
        .all()
    )
    if not attr_rows:
        extracted = extract_attributes(norm_txt, cls_row.category_code, material.manufacturer, material.part_number)
        for ext in extracted:
            row = MaterialAttribute(
                id=str(generate_uuidv7()),
                material_id=material.id,
                key=ext.key,
                raw_text=ext.raw_text,
                value_text=ext.value_text,
                value_num=ext.value_num,
                unit=ext.unit,
                canonical_value=ext.canonical_value,
                source=ext.source,
                confidence=ext.confidence,
                assumed=ext.assumed,
                internal_conflict=ext.internal_conflict,
                rule_id=ext.rule_id,
                is_current=True
            )
            db.add(row)
            attr_rows.append(row)

    db.commit()

    # Format attribute dict list for comparator
    attr_list = [
        {
            "key": a.key,
            "raw_text": a.raw_text,
            "value_text": a.value_text,
            "value_num": a.value_num,
            "canonical_value": a.canonical_value,
            "assumed": a.assumed,
            "internal_conflict": a.internal_conflict
        } for a in attr_rows
    ]

    return {
        "id": material.id,
        "cpse_id": material.cpse_id,
        "source_code": material.source_code,
        "raw_description": material.raw_description,
        "normalized_text": norm_txt,
        "category": cls_row.category_code,
        "category_code": cls_row.category_code,
        "category_confidence": cls_row.confidence,
        "uom_dimension": uom_dim,
        "manufacturer": material.manufacturer,
        "part_number": material.part_number,
        "attributes": attr_list
    }

def run_matching(
    db: Session,
    scope: dict,
    mode: str = "LIVE",
    user_id: str | None = None,
    candidate_cap: int = 20,
    run_id: str | None = None
) -> MatchRun:
    """
    Executes an end-to-end match run over the specified scope and persists results into PostgreSQL.
    Supports live progress reporting into the match_run.stats column.
    """
    start_time = time.time()
    bundle = load_config_bundle(db=db)

    # 1. Fetch or create MatchRun record
    match_run = None
    if run_id:
        match_run = db.query(MatchRun).filter_by(id=run_id).first()
        if match_run:
            match_run.status = "PROCESSING"
            match_run.started_at = datetime.now(timezone.utc)
            match_run.config_versions = {
                "scoring": bundle.scoring.get("version", 1),
                "abbreviations": "v1",
                "material_aliases": "v1",
                "standard_equivalence": "v1"
            }
            db.commit()

    if not match_run:
        run_id = str(generate_uuidv7())
        match_run = MatchRun(
            id=run_id,
            scope=scope,
            mode=mode,
            config_versions={
                "scoring": bundle.scoring.get("version", 1),
                "abbreviations": "v1",
                "material_aliases": "v1",
                "standard_equivalence": "v1"
            },
            status="PROCESSING",
            started_by=user_id,
            started_at=datetime.now(timezone.utc)
        )
        db.add(match_run)
        db.commit()

    try:
        # 2. Query target materials according to scope
        is_demo_run = bool(scope.get("is_demo") or mode in ["DEMO", "SIH_DEMO"])
        query = db.query(Material).filter(Material.status == "ACTIVE")
        if is_demo_run:
            candidate_cap = 8
            # Fast SIH Demo Run: sample ~45 materials across categories for a 2-second real execution
            targets = query.order_by(Material.id.asc()).limit(45).all()
        elif scope.get("batch_id"):
            targets = query.filter(Material.batch_id == scope["batch_id"]).all()
        elif scope.get("cpse_code"):
            cpse_row = db.query(Cpse).filter_by(code=scope["cpse_code"]).first()
            targets = query.filter(Material.cpse_id == cpse_row.id).all() if cpse_row else []
        elif scope.get("category"):
            targets = query.join(Classification, Classification.material_id == Material.id).filter(
                Classification.category_code == scope["category"],
                Classification.is_current == True
            ).all()
        else:
            targets = query.all()
        if not targets:
            match_run.status = "COMPLETED"
            match_run.finished_at = datetime.now(timezone.utc)
            match_run.stats = {
                "total_materials": 0,
                "materials_processed": 0,
                "candidates_retrieved": 0,
                "comparisons_performed": 0,
                "relationship_counts": {},
                "veto_count": 0,
                "duration_ms": int((time.time() - start_time) * 1000),
                "progress_pct": 100.0,
                "degraded": False
            }
            db.add(match_run)
            db.commit()
            return match_run

        # 3. Ensure target embeddings exist
        ensure_material_embeddings(db, targets)

        total_candidates = 0
        total_comparisons = 0
        veto_count = 0
        relationship_counts: dict[str, int] = {}
        evaluated_pairs_set: set[tuple[str, str]] = set()

        # Initialize progress stats immediately so dashboard / modal reflects real target counts
        match_run.stats = {
            "total_materials": len(targets),
            "materials_processed": 0,
            "candidates_retrieved": 0,
            "comparisons_performed": 0,
            "relationship_counts": {},
            "veto_count": 0,
            "duration_ms": int((time.time() - start_time) * 1000),
            "progress_pct": 0.0,
            "degraded": False
        }
        db.commit()

        reranker = get_reranker_provider(db=db)

        # 4. Process pairwise matching for each target material
        for idx, target in enumerate(targets):
            target_dict = _build_material_dict(db, target)
            cat_code = target_dict["category_code"]

            # Retrieve candidates via blocking & pgvector
            candidates, retrieval_method = get_candidate_materials(db, target, cat_code, candidate_cap=candidate_cap)
            total_candidates += len(candidates)

            if not candidates:
                continue

            # Optional Neural Reranking Stage (v2.1: retrieve -> rerank -> technical validation -> veto)
            rerank_scores_map: dict[str, float] = {}
            if reranker and len(candidates) >= 1:
                target_text = target.normalized_text or target.raw_description or ""
                pairs_to_score = [
                    (target_text, c.normalized_text or c.raw_description or "")
                    for c in candidates
                ]
                try:
                    scores = reranker.score_pairs(pairs_to_score)
                    scored_candidates = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
                    candidates = [c for c, _ in scored_candidates]
                    rerank_scores_map = {c.id: s for c, s in zip(candidates, scores)}
                except Exception:
                    pass

            # Ensure candidate embeddings exist
            ensure_material_embeddings(db, candidates)

            for candidate in candidates:
                if candidate.id == target.id:
                    continue

                # Ordered canonical pair to ensure symmetry and prevent duplicate reverse comparison
                id_a, id_b = sorted([target.id, candidate.id])
                pair_key = (id_a, id_b)
                if pair_key in evaluated_pairs_set:
                    continue
                evaluated_pairs_set.add(pair_key)

                # Check if match record already exists in DB for this pair under current run
                existing_match = db.query(MaterialMatch).filter_by(
                    material_a_id=id_a,
                    material_b_id=id_b,
                    run_id=run_id
                ).first()
                if existing_match:
                    continue

                mat_a_entity = target if target.id == id_a else candidate
                mat_b_entity = candidate if candidate.id == id_b else target

                mat_a_dict = _build_material_dict(db, mat_a_entity)
                mat_b_dict = _build_material_dict(db, mat_b_entity)

                # Execute Pairwise Engine (with optional neural rerank score)
                pair_rerank_score = rerank_scores_map.get(candidate.id)
                pair_res = evaluate_material_pair(mat_a_dict, mat_b_dict, rerank_score=pair_rerank_score)
                total_comparisons += 1

                if pair_res.veto.get("applied"):
                    veto_count += 1

                rel = pair_res.relationship
                relationship_counts[rel] = relationship_counts.get(rel, 0) + 1

                input_hash = hashlib.sha256(
                    f"{id_a}:{id_b}:{mat_a_dict['normalized_text']}:{mat_b_dict['normalized_text']}".encode("utf-8")
                ).hexdigest()

                # 5. Persist MaterialMatch
                match_row = MaterialMatch(
                    id=str(generate_uuidv7()),
                    run_id=run_id,
                    material_a_id=id_a,
                    material_b_id=id_b,
                    relationship=rel,
                    equivalence_confidence=pair_res.equivalence_confidence,
                    raw_score=pair_res.raw_score,
                    signals=pair_res.signals,
                    veto=pair_res.veto,
                    gates=pair_res.gates,
                    explanation=pair_res.explanation,
                    degraded=pair_res.degraded,
                    review_status="PROPOSED",
                    input_hash=input_hash
                )
                db.add(match_row)
                db.flush()

                # 6. Persist structured MatchEvidence rows
                ev_kinds = [
                    ("SEMANTIC", pair_res.signals.get("S", 0.0), None, {"score": pair_res.signals.get("S")}),
                    ("LEXICAL", pair_res.signals.get("L", 0.0), None, {"score": pair_res.signals.get("L")}),
                    ("ATTRIBUTE", pair_res.signals.get("A", 0.0), None, {"verdicts": pair_res.attribute_verdicts}),
                    ("CATEGORY", pair_res.signals.get("C", 0.0), None, {"cat_a": mat_a_dict["category"], "cat_b": mat_b_dict["category"]}),
                    ("GATE", 1.0 if not pair_res.veto.get("applied") else 0.0, "VETO" if pair_res.veto.get("applied") else "PASS", pair_res.veto)
                ]
                for ekind, escore, everdict, epayload in ev_kinds:
                    ev_row = MatchEvidence(
                        id=str(generate_uuidv7()),
                        match_id=match_row.id,
                        kind=ekind,
                        payload=epayload,
                        score=escore,
                        verdict=everdict
                    )
                    db.add(ev_row)

            # Flush periodic progress updates
            freq = 2 if is_demo_run else 5
            if (idx == 0) or ((idx + 1) % freq == 0) or ((idx + 1) == len(targets)):
                dur_ms = int((time.time() - start_time) * 1000)
                match_run.stats = {
                    "total_materials": len(targets),
                    "materials_processed": idx + 1,
                    "candidates_retrieved": total_candidates,
                    "comparisons_performed": total_comparisons,
                    "relationship_counts": dict(relationship_counts),
                    "veto_count": veto_count,
                    "duration_ms": dur_ms,
                    "progress_pct": round(((idx + 1) / len(targets)) * 100, 1),
                    "degraded": False
                }
                db.commit()

        db.commit()

        duration_ms = int((time.time() - start_time) * 1000)
        stats = {
            "total_materials": len(targets),
            "materials_processed": len(targets),
            "candidates_retrieved": total_candidates,
            "comparisons_performed": total_comparisons,
            "relationship_counts": relationship_counts,
            "veto_count": veto_count,
            "duration_ms": duration_ms,
            "progress_pct": 100.0,
            "degraded": False
        }

        match_run.status = "COMPLETED"
        match_run.finished_at = datetime.now(timezone.utc)
        match_run.stats = stats
        db.add(match_run)
        db.commit()
        db.refresh(match_run)

        # 7. Log audit event
        AuditService.record(
            db=db,
            actor_role="DATA_STEWARD",
            action="MATCH_RUN_COMPLETED",
            entity_type="match_run",
            entity_id=run_id,
            actor_id=user_id,
            after=stats,
            reason=f"Executed match run for {len(targets)} materials, {total_comparisons} comparisons performed."
        )

        return match_run

    except Exception as exc:
        db.rollback()
        fail_run = db.query(MatchRun).filter_by(id=run_id).first()
        if fail_run:
            fail_run.status = "FAILED"
            fail_run.finished_at = datetime.now(timezone.utc)
            fail_run.stats = {"error": str(exc), "trace": "Execution error during match run"}
            db.commit()
        raise exc

