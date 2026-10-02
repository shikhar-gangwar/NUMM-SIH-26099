from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float, BigInteger, DateTime,
    ForeignKey, UniqueConstraint, Index, CheckConstraint, JSON
)
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.db.base import Base
from app.core.ids import generate_uuidv7

class Cpse(Base):
    __tablename__ = "cpse"
    id = Column(String(36), primary_key=True, default=lambda: str(generate_uuidv7()))
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    sector = Column(String(100), nullable=True)
    is_synthetic = Column(Boolean, default=False, nullable=False)
    status = Column(String(20), default="ACTIVE", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class AppUser(Base):
    __tablename__ = "app_user"
    id = Column(String(36), primary_key=True, default=lambda: str(generate_uuidv7()))
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False) # SUPER_ADMIN, CPSE_ADMIN, DATA_STEWARD, REVIEWER, VIEWER
    cpse_id = Column(String(36), ForeignKey("cpse.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class ImportBatch(Base):
    __tablename__ = "import_batch"
    id = Column(String(36), primary_key=True, default=lambda: str(generate_uuidv7()))
    cpse_id = Column(String(36), ForeignKey("cpse.id"), nullable=False)
    kind = Column(String(20), nullable=False) # MATERIAL, PROCUREMENT
    filename = Column(String(255), nullable=False)
    sha256 = Column(String(64), nullable=False)
    total_rows = Column(Integer, default=0)
    accepted_rows = Column(Integer, default=0)
    rejected_rows = Column(Integer, default=0)
    warning_rows = Column(Integer, default=0)
    status = Column(String(30), default="RECEIVED", nullable=False)
    uploaded_by = Column(String(36), ForeignKey("app_user.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Material(Base):
    __tablename__ = "material"
    id = Column(String(36), primary_key=True, default=lambda: str(generate_uuidv7()))
    cpse_id = Column(String(36), ForeignKey("cpse.id"), nullable=False)
    source_code = Column(String(100), nullable=False)
    raw_description = Column(Text, nullable=False)
    raw_long_description = Column(Text, nullable=True)
    raw_uom = Column(String(50), nullable=False)
    category_hint = Column(String(100), nullable=True)
    manufacturer = Column(String(255), nullable=True)
    part_number = Column(String(100), nullable=True, index=True)
    batch_id = Column(String(36), ForeignKey("import_batch.id"), nullable=False)
    normalized_text = Column(Text, nullable=True)
    uom_canonical = Column(String(50), nullable=True)
    uom_dimension = Column(String(50), nullable=True)
    norm_flags = Column(JSON, nullable=True)
    status = Column(String(20), default="ACTIVE", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (
        UniqueConstraint("cpse_id", "source_code", name="uq_cpse_source_code"),
    )

class ModelVersion(Base):
    __tablename__ = "model_version"
    id = Column(String(36), primary_key=True, default=lambda: str(generate_uuidv7()))
    kind = Column(String(50), nullable=False) # EMBEDDING, RERANKER, LLM, CLASSIFIER, RULESET, CATEGORY_PACK, SCORING_CONFIG
    provider = Column(String(100), nullable=False)
    model_id = Column(String(255), nullable=False)
    model_version = Column(String(100), nullable=False)
    dimension = Column(Integer, nullable=True)
    params_hash = Column(String(64), nullable=True)
    config_hash = Column(String(64), nullable=True)
    registered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = Column(String(20), default="ACTIVE", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (
        UniqueConstraint("kind", "model_id", "model_version", "config_hash", name="uq_model_version_config"),
    )

class Category(Base):
    __tablename__ = "category"
    code = Column(String(50), primary_key=True)
    nmc_prefix = Column(String(10), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    pack_version_id = Column(String(36), ForeignKey("model_version.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Classification(Base):
    __tablename__ = "classification"
    id = Column(String(36), primary_key=True, default=lambda: str(generate_uuidv7()))
    material_id = Column(String(36), ForeignKey("material.id"), nullable=False)
    category_code = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    method = Column(String(50), nullable=False)
    runner_up = Column(String(50), nullable=True)
    candidates = Column(JSON, nullable=True)
    model_version_id = Column(String(36), ForeignKey("model_version.id"), nullable=True)
    ruleset_version_id = Column(String(36), ForeignKey("model_version.id"), nullable=True)
    input_hash = Column(String(64), nullable=False)
    is_current = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class MaterialAttribute(Base):
    __tablename__ = "material_attribute"
    id = Column(String(36), primary_key=True, default=lambda: str(generate_uuidv7()))
    material_id = Column(String(36), ForeignKey("material.id"), nullable=False)
    key = Column(String(100), nullable=False)
    raw_text = Column(Text, nullable=True)
    value_text = Column(Text, nullable=True)
    value_num = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)
    canonical_value = Column(Text, nullable=True)
    source = Column(String(30), nullable=False) # STRUCTURED, RULE, LLM, REVIEWER
    confidence = Column(Float, default=1.0)
    assumed = Column(Boolean, default=False)
    internal_conflict = Column(Boolean, default=False)
    span = Column(JSON, nullable=True)
    rule_id = Column(String(100), nullable=True)
    version_no = Column(Integer, default=1)
    supersedes_id = Column(String(36), ForeignKey("material_attribute.id"), nullable=True)
    is_current = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class MaterialEmbedding(Base):
    __tablename__ = "material_embedding"
    id = Column(String(36), primary_key=True, default=lambda: str(generate_uuidv7()))
    material_id = Column(String(36), ForeignKey("material.id"), nullable=False)
    model_version_id = Column(String(36), ForeignKey("model_version.id"), nullable=False)
    text_hash = Column(String(64), nullable=False)
    embedding = Column(Vector(384), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (
        UniqueConstraint("material_id", "model_version_id", name="uq_mat_embed_model"),
    )

class MatchRun(Base):
    __tablename__ = "match_run"
    id = Column(String(36), primary_key=True, default=lambda: str(generate_uuidv7()))
    scope = Column(JSON, nullable=True)
    mode = Column(String(20), default="LIVE", nullable=False) # LIVE, SHADOW
    config_versions = Column(JSON, nullable=True)
    stats = Column(JSON, nullable=True)
    status = Column(String(20), default="QUEUED", nullable=False)
    started_by = Column(String(36), ForeignKey("app_user.id"), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class MaterialMatch(Base):
    __tablename__ = "material_match"
    id = Column(String(36), primary_key=True, default=lambda: str(generate_uuidv7()))
    run_id = Column(String(36), ForeignKey("match_run.id"), nullable=False)
    material_a_id = Column(String(36), ForeignKey("material.id"), nullable=False)
    material_b_id = Column(String(36), ForeignKey("material.id"), nullable=False)
    relationship = Column(String(50), nullable=False)
    equivalence_confidence = Column(Float, nullable=False)
    raw_score = Column(Float, nullable=False)
    signals = Column(JSON, nullable=True)
    veto = Column(JSON, nullable=True)
    gates = Column(JSON, nullable=True)
    explanation = Column(Text, nullable=True)
    degraded = Column(Boolean, default=False)
    review_status = Column(String(30), default="PROPOSED", nullable=False)
    supersedes_match_id = Column(String(36), ForeignKey("material_match.id"), nullable=True)
    input_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (
        UniqueConstraint("material_a_id", "material_b_id", "run_id", name="uq_match_pair_run"),
        CheckConstraint("material_a_id < material_b_id", name="chk_match_pair_order"),
    )

class MatchEvidence(Base):
    __tablename__ = "match_evidence"
    id = Column(String(36), primary_key=True, default=lambda: str(generate_uuidv7()))
    match_id = Column(String(36), ForeignKey("material_match.id"), nullable=False)
    kind = Column(String(50), nullable=False) # SEMANTIC, LEXICAL, ATTRIBUTE, CATEGORY, RERANK, UOM, GATE, LLM
    payload = Column(JSON, nullable=True)
    score = Column(Float, nullable=True)
    verdict = Column(String(50), nullable=True)
    model_version_id = Column(String(36), ForeignKey("model_version.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class NationalMaterial(Base):
    __tablename__ = "national_material"
    uid = Column(String(36), primary_key=True, default=lambda: str(generate_uuidv7()))
    nmc = Column(String(50), unique=True, nullable=False)
    category_code = Column(String(50), nullable=False)
    status = Column(String(30), default="DRAFT", nullable=False)
    canonical_description = Column(Text, nullable=False)
    sap_short_description = Column(String(40), nullable=False)
    spec_fingerprint = Column(String(64), nullable=False)
    current_version_no = Column(Integer, default=1)
    superseded_by_uid = Column(String(36), ForeignKey("national_material.uid"), nullable=True)
    created_by_review_id = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class NationalMaterialVersion(Base):
    __tablename__ = "national_material_version"
    uid = Column(String(36), ForeignKey("national_material.uid"), primary_key=True)
    version_no = Column(Integer, primary_key=True)
    attributes = Column(JSON, nullable=False)
    canonical_description = Column(Text, nullable=False)
    fingerprint = Column(String(64), nullable=False)
    changed_by = Column(String(36), ForeignKey("app_user.id"), nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class NmcCounter(Base):
    __tablename__ = "nmc_counter"
    category_code = Column(String(50), primary_key=True)
    last_value = Column(BigInteger, default=0, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class LegacyMapping(Base):
    __tablename__ = "legacy_mapping"
    id = Column(String(36), primary_key=True, default=lambda: str(generate_uuidv7()))
    material_id = Column(String(36), ForeignKey("material.id"), nullable=False)
    national_material_uid = Column(String(36), ForeignKey("national_material.uid"), nullable=False)
    mapping_type = Column(String(30), nullable=False) # EXACT, NEAR, FUNCTIONAL, MANUAL
    status = Column(String(20), default="ACTIVE", nullable=False) # ACTIVE, CLOSED, REVOKED
    valid_from = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    valid_to = Column(DateTime(timezone=True), nullable=True)
    review_id = Column(String(36), nullable=True)
    closed_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Review(Base):
    __tablename__ = "review"
    id = Column(String(36), primary_key=True, default=lambda: str(generate_uuidv7()))
    match_id = Column(String(36), ForeignKey("material_match.id"), nullable=False)
    status = Column(String(30), nullable=False)
    decision = Column(String(30), nullable=False) # APPROVE, REJECT, MODIFY, ESCALATE, REVOKE
    reviewer_id = Column(String(36), ForeignKey("app_user.id"), nullable=False)
    ai_relationship = Column(String(50), nullable=False)
    human_relationship = Column(String(50), nullable=True)
    reason_code = Column(String(50), nullable=True)
    comment = Column(Text, nullable=True)
    evidence_snapshot = Column(JSON, nullable=True)
    claimed_by = Column(String(36), ForeignKey("app_user.id"), nullable=True)
    claimed_until = Column(DateTime(timezone=True), nullable=True)
    time_spent_ms = Column(Integer, nullable=True)
    decided_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class ProcurementRecord(Base):
    __tablename__ = "procurement_record"
    id = Column(String(36), primary_key=True, default=lambda: str(generate_uuidv7()))
    material_id = Column(String(36), ForeignKey("material.id"), nullable=False)
    po_date = Column(DateTime(timezone=True), nullable=False)
    quantity = Column(Float, nullable=False)
    uom = Column(String(50), nullable=False)
    quantity_canonical = Column(Float, nullable=True)
    unit_price = Column(Float, nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    vendor = Column(String(255), nullable=True)
    is_synthetic = Column(Boolean, default=False)
    batch_id = Column(String(36), ForeignKey("import_batch.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class AuditEvent(Base):
    __tablename__ = "audit_event"
    seq = Column(BigInteger, primary_key=True, autoincrement=True)
    ts = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    actor_id = Column(String(36), ForeignKey("app_user.id"), nullable=True)
    actor_role = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=False)
    before = Column(JSON, nullable=True)
    after = Column(JSON, nullable=True)
    reason = Column(Text, nullable=True)
    model_refs = Column(JSON, nullable=True)
    request_id = Column(String(100), nullable=True)
    prev_hash = Column(String(64), nullable=False)
    hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class JobRun(Base):
    __tablename__ = "job_run"
    id = Column(String(36), primary_key=True, default=lambda: str(generate_uuidv7()))
    type = Column(String(50), nullable=False)
    payload = Column(JSON, nullable=True)
    status = Column(String(20), default="QUEUED", nullable=False)
    progress = Column(Float, default=0.0)
    error = Column(Text, nullable=True)
    submitted_by = Column(String(36), ForeignKey("app_user.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IntegrationJob(Base):
    __tablename__ = "integration_job"
    id = Column(String(36), primary_key=True, default=lambda: str(generate_uuidv7()))
    adapter = Column(String(50), nullable=False)
    direction = Column(String(20), nullable=False) # EXPORT, SYNC
    payload_ref = Column(String(255), nullable=True)
    status = Column(String(20), default="QUEUED", nullable=False)
    counts = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    is_mock = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class SapMockMaterial(Base):
    __tablename__ = "sap_mock_material"
    id = Column(String(36), primary_key=True, default=lambda: str(generate_uuidv7()))
    sap_product_id = Column(String(40), unique=True, nullable=False)
    product_description = Column(String(40), nullable=False)
    nmc = Column(String(50), unique=True, nullable=False)
    payload = Column(JSON, nullable=True)
    status = Column(String(20), default="CREATED", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class UomConversion(Base):
    __tablename__ = "uom_conversion"
    from_unit = Column(String(50), primary_key=True)
    to_unit = Column(String(50), primary_key=True)
    factor = Column(Float, nullable=False)
    dimension = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
