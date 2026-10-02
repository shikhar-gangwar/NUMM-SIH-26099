from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.models import AuditEvent
from app.audit.hash_chain import GENESIS_HASH, compute_audit_hash, verify_hash_chain

class AuditService:
    @staticmethod
    def record(
        db: Session,
        actor_role: str,
        action: str,
        entity_type: str,
        entity_id: str,
        actor_id: str | None = None,
        before: dict | None = None,
        after: dict | None = None,
        reason: str | None = None,
        model_refs: dict | None = None,
        request_id: str | None = None
    ) -> AuditEvent:
        last_event = db.query(AuditEvent).order_by(AuditEvent.seq.desc()).first()
        prev_hash = last_event.hash if last_event else GENESIS_HASH
        
        # Calculate next seq
        next_seq = (last_event.seq + 1) if last_event else 1
        now_ts = datetime.now(timezone.utc)
        
        payload = {
            "seq": next_seq,
            "ts": now_ts.isoformat(),
            "actor_id": actor_id,
            "actor_role": actor_role,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "before": before,
            "after": after,
            "reason": reason,
            "model_refs": model_refs,
            "request_id": request_id
        }
        event_hash = compute_audit_hash(prev_hash, payload)
        
        event = AuditEvent(
            seq=next_seq,
            ts=now_ts,
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before=before,
            after=after,
            reason=reason,
            model_refs=model_refs,
            request_id=request_id,
            prev_hash=prev_hash,
            hash=event_hash
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def verify_all(db: Session) -> tuple[bool, int | None]:
        events = db.query(AuditEvent).order_by(AuditEvent.seq.asc()).all()
        return verify_hash_chain(events)
