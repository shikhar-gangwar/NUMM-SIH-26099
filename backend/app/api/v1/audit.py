from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import AuditEvent, AppUser
from app.audit.service import AuditService
from app.api.deps import require_role
from app.api.schemas.audit import AuditEventDTO, AuditVerifyResultDTO

router = APIRouter(prefix="/audit", tags=["Audit"])

@router.get("", response_model=List[AuditEventDTO])
def list_audit_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role(["DATA_STEWARD", "SUPER_ADMIN"]))
):
    query = db.query(AuditEvent)
    if action:
        query = query.filter_by(action=action)
    if entity_type:
        query = query.filter_by(entity_type=entity_type)
        
    events = query.order_by(AuditEvent.seq.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return [
        AuditEventDTO(
            seq=ev.seq,
            ts=ev.ts.isoformat(),
            actor_id=ev.actor_id,
            actor_role=ev.actor_role,
            action=ev.action,
            entity_type=ev.entity_type,
            entity_id=ev.entity_id,
            before=ev.before,
            after=ev.after,
            reason=ev.reason,
            model_refs=ev.model_refs,
            request_id=ev.request_id,
            prev_hash=ev.prev_hash,
            hash=ev.hash
        )
        for ev in events
    ]

@router.get("/verify", response_model=AuditVerifyResultDTO)
def verify_audit_chain(
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(require_role(["DATA_STEWARD", "SUPER_ADMIN"]))
):
    is_valid, broken_seq = AuditService.verify_all(db)
    total_events = db.query(AuditEvent).count()
    return AuditVerifyResultDTO(
        valid=is_valid,
        total_events=total_events,
        broken_seq=broken_seq,
        verified_at=datetime.now(timezone.utc).isoformat()
    )
