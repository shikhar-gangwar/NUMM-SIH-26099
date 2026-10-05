from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Dict
from datetime import datetime, timezone, timedelta
import threading

from app.db.session import get_db, SessionLocal
from app.db.models import Material, Cpse, MatchRun, MaterialMatch, MatchEvidence, Classification, MaterialAttribute, LegacyMapping, Review, AppUser, NationalMaterial
from app.api.deps import require_role
from app.api.schemas.material import MaterialDTO, AttributeValueDTO
from app.api.schemas.match import MatchRunCreateDTO, MatchRunResponseDTO, MatchRunActiveStatusDTO, PairResultDTO, MatchEvidenceDTO
from app.matching.orchestrator import run_matching
from app.core.ids import generate_uuidv7

router = APIRouter(tags=["Matching & Evidence"])

def _build_review_details(db: Session, match_id: str) -> Optional[Dict[str, Any]]:
    rev = db.query(Review).filter_by(match_id=match_id).order_by(Review.created_at.desc()).first()
    if not rev:
        return None
    user = db.query(AppUser).filter_by(id=rev.reviewer_id).first()
    leg = db.query(LegacyMapping).filter_by(review_id=match_id).first()
    target_nmc = None
    if leg:
        nat = db.query(NationalMaterial).filter_by(uid=leg.national_material_uid).first()
        if nat:
            target_nmc = nat.nmc

    return {
        "decision": rev.decision,
        "decided_by": user.username if user else "steward_admin",
        "role": user.role if user else "SUPER_ADMIN",
        "decided_at": rev.decided_at.isoformat() if rev.decided_at else None,
        "reason_code": rev.reason_code,
        "comment": rev.comment,
        "target_nmc": target_nmc
    }

def _to_material_dto(db: Session, mat: Material) -> MaterialDTO:
    cpse = db.query(Cpse).filter_by(id=mat.cpse_id).first()
    cls_row = db.query(Classification).filter_by(material_id=mat.id, is_current=True).first()
    attrs = db.query(MaterialAttribute).filter_by(material_id=mat.id, is_current=True).all()
    mapping = db.query(LegacyMapping).filter_by(material_id=mat.id, status="ACTIVE").first()
    mapping_nmc = None
    if mapping:
        nat_mat = db.query(NationalMaterial).filter_by(uid=mapping.national_material_uid).first()
        mapping_nmc = nat_mat.nmc if nat_mat else mapping.national_material_uid

    attr_dtos = [
        AttributeValueDTO(
            key=a.key,
            raw_text=a.raw_text,
            value=a.canonical_value or a.value_text or a.value_num,
            unit=a.unit,
            canonical_value=a.canonical_value,
            source=a.source,
            confidence=a.confidence,
            span=a.span,
            rule_id=a.rule_id,
            assumed=a.assumed,
            internal_conflict=a.internal_conflict
        ) for a in attrs
    ]

    return MaterialDTO(
        id=mat.id,
        cpse_code=cpse.code if cpse else "UNKNOWN",
        source_code=mat.source_code,
        raw_description=mat.raw_description,
        raw_uom=mat.raw_uom,
        normalized_text=mat.normalized_text,
        uom_canonical=mat.uom_canonical,
        uom_dimension=mat.uom_dimension,
        category_code=cls_row.category_code if cls_row else mat.category_hint,
        category_confidence=cls_row.confidence if cls_row else 1.0,
        attributes=attr_dtos,
        mapping_nmc=mapping_nmc,
        mapping_status=mapping.status if mapping else None,
        manufacturer=mat.manufacturer,
        part_number=mat.part_number,
        provenance=getattr(mat, "provenance", "SYNTHETIC_DEMO"),
        provenance_metadata=getattr(mat, "provenance_metadata", None),
        created_at=mat.created_at,
        status=mat.status
    )

def _to_match_run_dto(r: MatchRun) -> MatchRunResponseDTO:
    stats = dict(r.stats) if r.stats else {}
    if stats:
        if "total_materials" not in stats and "materials_processed" in stats:
            stats["total_materials"] = stats["materials_processed"]
        if "materials_processed" not in stats and "total_materials" in stats:
            stats["materials_processed"] = stats["total_materials"]
        if "comparisons_performed" not in stats:
            stats["comparisons_performed"] = 0
        if "veto_count" not in stats:
            stats["veto_count"] = 0
        if "duration_ms" not in stats and r.started_at and r.finished_at:
            stats["duration_ms"] = int((r.finished_at - r.started_at).total_seconds() * 1000)

    return MatchRunResponseDTO(
        id=r.id,
        scope=r.scope,
        mode=r.mode,
        config_versions=r.config_versions,
        stats=stats if stats else None,
        status=r.status,
        started_by=r.started_by,
        started_at=r.started_at,
        finished_at=r.finished_at
    )

@router.get("/matching/status/active", response_model=MatchRunActiveStatusDTO)
def get_active_match_run_status(
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["VIEWER", "REVIEWER", "DATA_STEWARD", "SUPER_ADMIN"]))
):
    """
    Returns current active running job status (if any) and the last completed match run for dashboard display.
    """
    fifteen_min_ago = datetime.now(timezone.utc) - timedelta(minutes=15)
    active_run = db.query(MatchRun).filter(
        MatchRun.status.in_(["QUEUED", "PROCESSING"]),
        MatchRun.created_at >= fifteen_min_ago
    ).order_by(MatchRun.created_at.desc()).first()

    # Prioritize completed runs that have finished_at and non-empty stats
    last_completed = db.query(MatchRun).filter(
        MatchRun.status == "COMPLETED",
        MatchRun.finished_at.isnot(None),
        MatchRun.stats.isnot(None)
    ).order_by(MatchRun.finished_at.desc()).first()

    if not last_completed:
        last_completed = db.query(MatchRun).filter(
            MatchRun.status == "COMPLETED",
            MatchRun.finished_at.isnot(None)
        ).order_by(MatchRun.finished_at.desc()).first()

    if not last_completed:
        last_completed = db.query(MatchRun).filter_by(
            status="COMPLETED"
        ).order_by(MatchRun.created_at.desc()).first()

    return MatchRunActiveStatusDTO(
        is_active=active_run is not None,
        current_run=_to_match_run_dto(active_run) if active_run else None,
        last_completed_run=_to_match_run_dto(last_completed) if last_completed else None
    )

def _background_match_worker(run_id: str, scope: dict, mode: str, user_id: str):
    worker_db = SessionLocal()
    try:
        run_matching(
            db=worker_db,
            scope=scope,
            mode=mode,
            user_id=user_id,
            run_id=run_id
        )
    except Exception as exc:
        print(f"[MatchWorker Error] run {run_id} failed: {exc}", flush=True)
        try:
            run = worker_db.query(MatchRun).filter_by(id=run_id).first()
            if run and run.status in ["QUEUED", "PROCESSING"]:
                run.status = "FAILED"
                run.finished_at = datetime.now(timezone.utc)
                stats = dict(run.stats) if run.stats else {}
                stats["error"] = str(exc)
                run.stats = stats
                worker_db.commit()
        except Exception as e2:
            print(f"[MatchWorker Error] Failed to record error state: {e2}", flush=True)
    finally:
        worker_db.close()

@router.post("/matching/runs", response_model=MatchRunResponseDTO, status_code=status.HTTP_202_ACCEPTED)
def create_match_run(
    req: MatchRunCreateDTO,
    async_mode: bool = Query(False, description="Set True for non-blocking background execution"),
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["DATA_STEWARD", "SUPER_ADMIN"]))
):
    """
    Triggers an end-to-end match run over the target scope (batch_id, cpse_code, or all).
    Enforces a concurrency lock to prevent overlapping runs.
    """
    # 1. Concurrency Check
    fifteen_min_ago = datetime.now(timezone.utc) - timedelta(minutes=15)
    active_run = db.query(MatchRun).filter(
        MatchRun.status.in_(["QUEUED", "PROCESSING"]),
        MatchRun.started_at >= fifteen_min_ago
    ).order_by(MatchRun.started_at.desc()).first()

    if active_run:
        if req.force:
            active_run.status = "CANCELLED"
            active_run.finished_at = datetime.now(timezone.utc)
            db.commit()
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "CONCURRENT_RUN_IN_PROGRESS",
                    "message": "A match run is already in progress. Concurrent runs are locked to prevent resource thrashing.",
                    "active_run_id": active_run.id,
                    "status": active_run.status
                }
            )

    # 2. Async vs Sync Execution
    effective_scope = req.scope if req.scope is not None else {}
    run_mode = req.mode or "LIVE"

    if async_mode:
        run_id = str(generate_uuidv7())
        match_run = MatchRun(
            id=run_id,
            scope=effective_scope,
            mode=run_mode,
            status="QUEUED",
            started_by=current_user.id,
            started_at=datetime.now(timezone.utc)
        )
        db.add(match_run)
        db.commit()
        db.refresh(match_run)

        # Launch in background thread with clean DB session
        th = threading.Thread(
            target=_background_match_worker,
            args=(run_id, effective_scope, run_mode, current_user.id),
            daemon=True
        )
        th.start()

        return _to_match_run_dto(match_run)
    else:
        # Synchronous execution
        match_run = run_matching(
            db=db,
            scope=effective_scope,
            mode=run_mode,
            user_id=current_user.id
        )
        return _to_match_run_dto(match_run)


@router.post("/matching/runs/{run_id}/cancel", response_model=MatchRunResponseDTO)
def cancel_match_run(
    run_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["DATA_STEWARD", "SUPER_ADMIN"]))
):
    """
    Terminates or marks an active match run as CANCELLED to release locks.
    """
    run = db.query(MatchRun).filter_by(id=run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Match run not found")
    if run.status in ["QUEUED", "PROCESSING"]:
        run.status = "CANCELLED"
        run.finished_at = datetime.now(timezone.utc)
        if run.stats:
            stats = dict(run.stats)
            stats["error"] = "Cancelled by user"
            run.stats = stats
        db.commit()
    return _to_match_run_dto(run)


@router.post("/matching/runs/reset-active", response_model=Dict[str, Any])
def reset_active_match_runs(
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["DATA_STEWARD", "SUPER_ADMIN"]))
):
    """
    Force-clears any active QUEUED or PROCESSING match runs to release engine locks.
    """
    active_runs = db.query(MatchRun).filter(
        MatchRun.status.in_(["QUEUED", "PROCESSING"])
    ).all()
    count = 0
    now = datetime.now(timezone.utc)
    for r in active_runs:
        r.status = "CANCELLED"
        r.finished_at = now
        count += 1
    db.commit()
    return {"status": "ok", "cleared_runs": count}


@router.get("/matching/runs", response_model=List[MatchRunResponseDTO])
def list_match_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["VIEWER", "REVIEWER", "DATA_STEWARD", "SUPER_ADMIN"]))
):
    offset = (page - 1) * page_size
    runs = db.query(MatchRun).order_by(MatchRun.created_at.desc()).offset(offset).limit(page_size).all()
    return [
        MatchRunResponseDTO(
            id=r.id,
            scope=r.scope,
            mode=r.mode,
            config_versions=r.config_versions,
            stats=r.stats,
            status=r.status,
            started_by=r.started_by,
            started_at=r.started_at,
            finished_at=r.finished_at
        ) for r in runs
    ]

@router.get("/matching/runs/{run_id}", response_model=MatchRunResponseDTO)
def get_match_run(
    run_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["VIEWER", "REVIEWER", "DATA_STEWARD", "SUPER_ADMIN"]))
):
    r = db.query(MatchRun).filter_by(id=run_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Match run not found")
    return MatchRunResponseDTO(
        id=r.id,
        scope=r.scope,
        mode=r.mode,
        config_versions=r.config_versions,
        stats=r.stats,
        status=r.status,
        started_by=r.started_by,
        started_at=r.started_at,
        finished_at=r.finished_at
    )

@router.get("/matches", response_model=List[PairResultDTO])
def list_matches(
    run_id: Optional[str] = None,
    relationship: Optional[str] = None,
    review_status: Optional[str] = None,
    has_veto: Optional[bool] = None,
    min_conf: Optional[float] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["VIEWER", "REVIEWER", "DATA_STEWARD", "SUPER_ADMIN"]))
):
    query = db.query(MaterialMatch)
    if run_id:
        query = query.filter(MaterialMatch.run_id == run_id)
    if relationship:
        query = query.filter(MaterialMatch.relationship == relationship)
    if review_status:
        query = query.filter(MaterialMatch.review_status == review_status)
    if min_conf is not None:
        query = query.filter(MaterialMatch.equivalence_confidence >= min_conf)

    offset = (page - 1) * page_size
    matches = query.order_by(MaterialMatch.created_at.desc()).offset(offset).limit(page_size * 2).all()

    results = []
    for m in matches:
        if len(results) >= page_size:
            break
        if has_veto is True and not (m.veto and m.veto.get("applied")):
            continue
        if has_veto is False and (m.veto and m.veto.get("applied")):
            continue

        mat_a = db.query(Material).filter_by(id=m.material_a_id).first()
        mat_b = db.query(Material).filter_by(id=m.material_b_id).first()
        if not mat_a or not mat_b:
            continue

        ev_rows = db.query(MatchEvidence).filter_by(match_id=m.id).all()
        ev_dtos = [
            MatchEvidenceDTO(
                id=e.id,
                match_id=e.match_id,
                kind=e.kind,
                payload=e.payload,
                score=e.score,
                verdict=e.verdict
            ) for e in ev_rows
        ]

        results.append(
            PairResultDTO(
                id=m.id,
                run_id=m.run_id,
                material_a=_to_material_dto(db, mat_a),
                material_b=_to_material_dto(db, mat_b),
                relationship=m.relationship,
                equivalence_confidence=m.equivalence_confidence,
                raw_score=m.raw_score,
                signals=m.signals,
                veto=m.veto,
                gates=m.gates,
                explanation=m.explanation,
                degraded=m.degraded,
                review_status=m.review_status,
                evidence=ev_dtos,
                fingerprints={"ruleset": "v1"}
            )
        )

    return results

@router.get("/matches/{match_id}", response_model=PairResultDTO)
def get_match_detail(
    match_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["VIEWER", "REVIEWER", "DATA_STEWARD", "SUPER_ADMIN"]))
):
    m = db.query(MaterialMatch).filter_by(id=match_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")

    mat_a = db.query(Material).filter_by(id=m.material_a_id).first()
    mat_b = db.query(Material).filter_by(id=m.material_b_id).first()
    if not mat_a or not mat_b:
        raise HTTPException(status_code=404, detail="Material entities not found for match")

    ev_rows = db.query(MatchEvidence).filter_by(match_id=m.id).all()
    ev_dtos = [
        MatchEvidenceDTO(
            id=e.id,
            match_id=e.match_id,
            kind=e.kind,
            payload=e.payload,
            score=e.score,
            verdict=e.verdict
        ) for e in ev_rows
    ]

    return PairResultDTO(
        id=m.id,
        run_id=m.run_id,
        material_a=_to_material_dto(db, mat_a),
        material_b=_to_material_dto(db, mat_b),
        relationship=m.relationship,
        equivalence_confidence=m.equivalence_confidence,
        raw_score=m.raw_score,
        signals=m.signals,
        veto=m.veto,
        gates=m.gates,
        explanation=m.explanation,
        degraded=m.degraded,
        review_status=m.review_status,
        evidence=ev_dtos,
        fingerprints={"ruleset": "v1"},
        review_details=_build_review_details(db, m.id)
    )
