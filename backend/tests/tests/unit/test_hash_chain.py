from app.audit.service import AuditService
from app.audit.hash_chain import verify_hash_chain

def test_audit_hash_chain(db_session):
    ev1 = AuditService.record(
        db=db_session,
        actor_role="SUPER_ADMIN",
        action="SYSTEM_INIT",
        entity_type="SYSTEM",
        entity_id="1"
    )
    assert ev1.seq == 1
    assert ev1.prev_hash == "0000000000000000000000000000000000000000000000000000000000000000"
    
    ev2 = AuditService.record(
        db=db_session,
        actor_role="DATA_STEWARD",
        action="CONFIG_LOAD",
        entity_type="CONFIG",
        entity_id="scoring.yaml"
    )
    assert ev2.seq == 2
    assert ev2.prev_hash == ev1.hash
    
    is_valid, broken_seq = AuditService.verify_all(db_session)
    assert is_valid is True
    assert broken_seq is None
