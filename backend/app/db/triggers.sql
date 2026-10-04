-- Triggers & Constraints DDL for SIH Unified Material Master DB

-- 1. Extension initializations
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 2. Material source fields immutability trigger
CREATE OR REPLACE FUNCTION check_material_immutability()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'UPDATE') THEN
        IF NEW.source_code <> OLD.source_code OR
           NEW.raw_description <> OLD.raw_description OR
           NEW.raw_uom <> OLD.raw_uom OR
           NEW.cpse_id <> OLD.cpse_id THEN
            RAISE EXCEPTION 'Material source fields (source_code, raw_description, raw_uom, cpse_id) are immutable and cannot be updated.';
        END IF;
    ELSIF (TG_OP = 'DELETE') THEN
        RAISE EXCEPTION 'Material records cannot be deleted.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_material_immutability ON material;
CREATE TRIGGER trg_material_immutability
BEFORE UPDATE OR DELETE ON material
FOR EACH ROW EXECUTE FUNCTION check_material_immutability();

-- 3. Audit log immutability trigger
CREATE OR REPLACE FUNCTION check_audit_immutability()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit event rows are append-only. UPDATE and DELETE operations are forbidden.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_immutability ON audit_event;
CREATE TRIGGER trg_audit_immutability
BEFORE UPDATE OR DELETE ON audit_event
FOR EACH ROW EXECUTE FUNCTION check_audit_immutability();

-- 4. Partial unique indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_legacy_mapping_active_unique 
ON legacy_mapping (material_id) 
WHERE valid_to IS NULL AND status = 'ACTIVE';

CREATE UNIQUE INDEX IF NOT EXISTS idx_national_material_fingerprint_unique 
ON national_material (category_code, spec_fingerprint) 
WHERE status IN ('DRAFT', 'ACTIVE');

-- 5. pgvector HNSW index on material_embedding
CREATE INDEX IF NOT EXISTS idx_material_embedding_hnsw 
ON material_embedding USING hnsw (embedding vector_cosine_ops);

