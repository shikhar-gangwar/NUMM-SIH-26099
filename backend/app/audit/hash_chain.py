from datetime import datetime, timezone
import hashlib
import json

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

def format_ts_canonical(ts) -> str:
    if isinstance(ts, str):
        ts_clean = ts.replace("Z", "+00:00").replace(" ", "T")
        try:
            ts = datetime.fromisoformat(ts_clean)
        except ValueError:
            return ts
    
    if hasattr(ts, "tzinfo") and ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    elif hasattr(ts, "astimezone"):
        ts = ts.astimezone(timezone.utc)
        
    return ts.strftime("%Y-%m-%dT%H:%M:%S.%f")

def compute_audit_hash(prev_hash: str, payload: dict) -> str:
    """Compute SHA-256 hash for an audit event: sha256(prev_hash || canonical_json(payload))"""
    canonical_payload = json.dumps(payload, sort_keys=True)
    combined = f"{prev_hash}{canonical_payload}".encode("utf-8")
    return hashlib.sha256(combined).hexdigest()

def verify_hash_chain(events: list) -> tuple[bool, int | None]:
    """Verify integrity of a sequence of audit event ORM objects. Returns (is_valid, broken_seq)"""
    current_prev = GENESIS_HASH
    for ev in events:
        if ev.prev_hash != current_prev:
            return False, ev.seq
        
        payload = {
            "seq": ev.seq,
            "ts": format_ts_canonical(ev.ts),
            "actor_id": ev.actor_id,
            "actor_role": ev.actor_role,
            "action": ev.action,
            "entity_type": ev.entity_type,
            "entity_id": ev.entity_id,
            "before": ev.before,
            "after": ev.after,
            "reason": ev.reason,
            "model_refs": ev.model_refs,
            "request_id": ev.request_id
        }
        computed = compute_audit_hash(current_prev, payload)
        if computed != ev.hash:
            return False, ev.seq
        current_prev = ev.hash
        
    return True, None
