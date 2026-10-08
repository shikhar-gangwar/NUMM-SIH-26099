"""
Deterministic Golden Review Demonstration Scenarios
SIH 2026 PS 26099 — CPSE Material Code Harmonisation

Ensures verified benchmark demonstration examples in the review queue:
- 10 SAFE EQUIVALENT examples (covering BOLT, PIPE, BEARING, VALVE, GASKET, CABLE)
- 10 CRITICAL CONFLICT examples (covering genuine engineering conflicts: 8.8 vs 10.9, SS304 vs SS316, etc.)
- 10 REVIEW REQUIRED examples (covering missing/unknown critical attributes under Gate G4)

All scores are calculated through the actual matching engine (evaluate_material_pair).
"""

import os
import sys
import hashlib
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres:postgres@localhost:5433/sih_master"

from app.db.session import SessionLocal
from app.db.models import Material, MaterialMatch, MatchRun, Cpse, Classification, ImportBatch, AppUser
from app.normalization.text import normalize_text
from app.normalization.uom import normalize_uom
from app.extraction.extractor import detect_category, extract_attributes
from app.matching.engine import evaluate_material_pair
from app.core.ids import generate_uuidv7

DEMO_SCENARIOS = [
    # ==================== 10 SAFE EQUIVALENT EXAMPLES ====================
    {
        "category": "BOLT",
        "code_a": "GOLDEN-SAFE-BOLT-01A",
        "desc_a": "BOLT HEX M12 X 60 SS316 GRADE 8.8 ISO 4014",
        "cpse_a": "OIL_INDIA",
        "code_b": "GOLDEN-SAFE-BOLT-01B",
        "desc_b": "HEX HEAD BOLT M12-1.75 X 60 MM SS316 CLASS 8.8 DIN 931",
        "cpse_b": "NTPC",
        "uom": "EA",
        "expected_rel": "FUNCTIONALLY_EQUIVALENT"
    },
    {
        "category": "PIPE",
        "code_a": "GOLDEN-SAFE-PIPE-02A",
        "desc_a": "PIPE 4 INCH SCH 40 SEAMLESS ASTM A106 GRADE B BEVELED",
        "cpse_a": "OIL_INDIA",
        "code_b": "GOLDEN-SAFE-PIPE-02B",
        "desc_b": "SEAMLESS PIPE 4 IN SCH 40 A106 GR B PLAIN END",
        "cpse_b": "IOCL",
        "uom": "MTR",
        "expected_rel": "FUNCTIONALLY_EQUIVALENT"
    },
    {
        "category": "BEARING",
        "code_a": "GOLDEN-SAFE-BRG-03A",
        "desc_a": "BEARING 6205 2RS C3 DEEP GROOVE BALL BEARING",
        "cpse_a": "NTPC",
        "code_b": "GOLDEN-SAFE-BRG-03B",
        "desc_b": "DEEP GROOVE BALL BEARING 6205-2RS C3 SKF",
        "cpse_b": "IOCL",
        "uom": "EA",
        "expected_rel": "EXACT_DUPLICATE"
    },
    {
        "category": "VALVE",
        "code_a": "GOLDEN-SAFE-VLV-04A",
        "desc_a": "GATE VALVE 2 INCH CLASS 150 FLANGED WCB",
        "cpse_a": "OIL_INDIA",
        "code_b": "GOLDEN-SAFE-VLV-04B",
        "desc_b": "FLANGED GATE VALVE 2 IN CL 150 BODY WCB",
        "cpse_b": "NTPC",
        "uom": "EA",
        "expected_rel": "EXACT_DUPLICATE"
    },
    {
        "category": "GASKET",
        "code_a": "GOLDEN-SAFE-GSKT-05A",
        "desc_a": "SPIRAL WOUND GASKET 4 INCH CLASS 150 SS316 GRAPHITE",
        "cpse_a": "IOCL",
        "code_b": "GOLDEN-SAFE-GSKT-05B",
        "desc_b": "SW GASKET 4 IN CL 150 SS316/GRAPHITE FILLER",
        "cpse_b": "OIL_INDIA",
        "uom": "EA",
        "expected_rel": "EXACT_DUPLICATE"
    },
    {
        "category": "CABLE",
        "code_a": "GOLDEN-SAFE-CBL-06A",
        "desc_a": "CABLE 4C X 16 SQMM COPPER XLPE 1.1KV ARMOURED",
        "cpse_a": "NTPC",
        "code_b": "GOLDEN-SAFE-CBL-06B",
        "desc_b": "LT POWER CABLE 4 CORE 16 SQ MM CU XLPE ARMOURED 1100V",
        "cpse_b": "IOCL",
        "uom": "MTR",
        "expected_rel": "FUNCTIONALLY_EQUIVALENT"
    },
    {
        "category": "BOLT",
        "code_a": "GOLDEN-SAFE-BOLT-07A",
        "desc_a": "STUD BOLT M20 X 100 ALLOY STEEL ASTM A193 B7",
        "cpse_a": "OIL_INDIA",
        "code_b": "GOLDEN-SAFE-BOLT-07B",
        "desc_b": "ALLOY STEEL STUD BOLT M20X100 GR B7 WITH 2 HEX NUTS",
        "cpse_b": "IOCL",
        "uom": "SET",
        "expected_rel": "FUNCTIONALLY_EQUIVALENT"
    },
    {
        "category": "PIPE",
        "code_a": "GOLDEN-SAFE-PIPE-08A",
        "desc_a": "PIPE 2 INCH SCH 80 SEAMLESS ASTM A333 GR 6 LOW TEMP",
        "cpse_a": "NTPC",
        "code_b": "GOLDEN-SAFE-PIPE-08B",
        "desc_b": "SEAMLESS STEEL PIPE 2 INCH SCH 80 ASTM A333 GRADE 6",
        "cpse_b": "OIL_INDIA",
        "uom": "MTR",
        "expected_rel": "FUNCTIONALLY_EQUIVALENT"
    },
    {
        "category": "BEARING",
        "code_a": "GOLDEN-SAFE-BRG-09A",
        "desc_a": "BEARING 6308 ZZ C3 DEEP GROOVE BALL BEARING",
        "cpse_a": "IOCL",
        "code_b": "GOLDEN-SAFE-BRG-09B",
        "desc_b": "BALL BEARING 6308-ZZ C3 SHIELDED FAG",
        "cpse_b": "NTPC",
        "uom": "EA",
        "expected_rel": "EXACT_DUPLICATE"
    },
    {
        "category": "VALVE",
        "code_a": "GOLDEN-SAFE-VLV-10A",
        "desc_a": "BALL VALVE 1 INCH CLASS 300 FLANGED SS316",
        "cpse_a": "OIL_INDIA",
        "code_b": "GOLDEN-SAFE-VLV-10B",
        "desc_b": "FLANGED BALL VALVE 1 IN CL 300 SS316 BODY",
        "cpse_b": "IOCL",
        "uom": "EA",
        "expected_rel": "EXACT_DUPLICATE"
    },

    # ==================== 10 CRITICAL CONFLICT EXAMPLES (G2 VETO) ====================
    {
        "category": "BOLT",
        "code_a": "GOLDEN-CONF-BOLT-11A",
        "desc_a": "BOLT HEX M12 X 60 GRADE 8.8 CARBON STEEL",
        "cpse_a": "OIL_INDIA",
        "code_b": "GOLDEN-CONF-BOLT-11B",
        "desc_b": "HEX BOLT M12 X 60 GRADE 10.9 HIGH TENSILE",
        "cpse_b": "NTPC",
        "uom": "EA",
        "expected_rel": "NOT_EQUIVALENT",
        "conflict_reason": "Gate G2: Property class conflict (8.8 != 10.9)"
    },
    {
        "category": "BOLT",
        "code_a": "GOLDEN-CONF-BOLT-12A",
        "desc_a": "HEX BOLT M10 X 50 SS304 GRADE 8.8",
        "cpse_a": "NTPC",
        "code_b": "GOLDEN-CONF-BOLT-12B",
        "desc_b": "HEX BOLT M16 X 50 SS304 GRADE 8.8",
        "cpse_b": "IOCL",
        "uom": "EA",
        "expected_rel": "NOT_EQUIVALENT",
        "conflict_reason": "Gate G2: Nominal diameter conflict (M10 != M16)"
    },
    {
        "category": "PIPE",
        "code_a": "GOLDEN-CONF-PIPE-13A",
        "desc_a": "PIPE 4 INCH SCH 40 SEAMLESS ASTM A106 GR B",
        "cpse_a": "OIL_INDIA",
        "code_b": "GOLDEN-CONF-PIPE-13B",
        "desc_b": "PIPE 4 INCH SCH 80 SEAMLESS ASTM A106 GR B",
        "cpse_b": "IOCL",
        "uom": "MTR",
        "expected_rel": "NOT_EQUIVALENT",
        "conflict_reason": "Gate G2: Pipe schedule/wall thickness conflict (SCH 40 != SCH 80)"
    },
    {
        "category": "PIPE",
        "code_a": "GOLDEN-CONF-PIPE-14A",
        "desc_a": "SEAMLESS PIPE 2 INCH SCH 40 ASTM A106 GR B",
        "cpse_a": "NTPC",
        "code_b": "GOLDEN-CONF-PIPE-14B",
        "desc_b": "SEAMLESS PIPE 4 INCH SCH 40 ASTM A106 GR B",
        "cpse_b": "OIL_INDIA",
        "uom": "MTR",
        "expected_rel": "NOT_EQUIVALENT",
        "conflict_reason": "Gate G2: Nominal pipe diameter conflict (2 IN != 4 IN)"
    },
    {
        "category": "VALVE",
        "code_a": "GOLDEN-CONF-VLV-15A",
        "desc_a": "GATE VALVE 2 INCH CLASS 150 FLANGED WCB",
        "cpse_a": "OIL_INDIA",
        "code_b": "GOLDEN-CONF-VLV-15B",
        "desc_b": "GATE VALVE 2 INCH CLASS 300 FLANGED WCB",
        "cpse_b": "IOCL",
        "uom": "EA",
        "expected_rel": "NOT_EQUIVALENT",
        "conflict_reason": "Gate G2: Pressure rating conflict (CLASS 150 != CLASS 300)"
    },
    {
        "category": "VALVE",
        "code_a": "GOLDEN-CONF-VLV-16A",
        "desc_a": "GLOBE VALVE 3 INCH CLASS 150 FLANGED WCB",
        "cpse_a": "NTPC",
        "code_b": "GOLDEN-CONF-VLV-16B",
        "desc_b": "CHECK VALVE 3 INCH CLASS 150 FLANGED WCB",
        "cpse_b": "OIL_INDIA",
        "uom": "EA",
        "expected_rel": "NOT_EQUIVALENT",
        "conflict_reason": "Gate G2: Valve functional mechanism conflict (GLOBE != CHECK)"
    },
    {
        "category": "BEARING",
        "code_a": "GOLDEN-CONF-BRG-17A",
        "desc_a": "DEEP GROOVE BALL BEARING 6205 2RS C3",
        "cpse_a": "IOCL",
        "code_b": "GOLDEN-CONF-BRG-17B",
        "desc_b": "DEEP GROOVE BALL BEARING 6308 2RS C3",
        "cpse_b": "NTPC",
        "uom": "EA",
        "expected_rel": "NOT_EQUIVALENT",
        "conflict_reason": "Gate G2: Dimensional base mismatch (25mm ID vs 40mm ID)"
    },
    {
        "category": "GASKET",
        "code_a": "GOLDEN-CONF-GSKT-18A",
        "desc_a": "SPIRAL WOUND GASKET 4 INCH CLASS 150 SS316 GRAPHITE",
        "cpse_a": "OIL_INDIA",
        "code_b": "GOLDEN-CONF-GSKT-18B",
        "desc_b": "SPIRAL WOUND GASKET 4 INCH CLASS 300 SS316 GRAPHITE",
        "cpse_b": "IOCL",
        "uom": "EA",
        "expected_rel": "NOT_EQUIVALENT",
        "conflict_reason": "Gate G2: Pressure class conflict (CLASS 150 != CLASS 300)"
    },
    {
        "category": "CABLE",
        "code_a": "GOLDEN-CONF-CBL-19A",
        "desc_a": "POWER CABLE 4C X 16 SQMM COPPER XLPE 1.1KV ARMOURED",
        "cpse_a": "NTPC",
        "code_b": "GOLDEN-CONF-CBL-19B",
        "desc_b": "POWER CABLE 4C X 16 SQMM ALUMINIUM XLPE 1.1KV ARMOURED",
        "cpse_b": "OIL_INDIA",
        "uom": "MTR",
        "expected_rel": "NOT_EQUIVALENT",
        "conflict_reason": "Gate G2: Conductor metallurgy conflict (COPPER != ALUMINIUM)"
    },
    {
        "category": "CABLE",
        "code_a": "GOLDEN-CONF-CBL-20A",
        "desc_a": "HT CABLE 3C X 185 SQMM ALUMINIUM XLPE 11KV ARMOURED",
        "cpse_a": "IOCL",
        "code_b": "GOLDEN-CONF-CBL-20B",
        "desc_b": "LT CABLE 3C X 185 SQMM ALUMINIUM XLPE 1.1KV ARMOURED",
        "cpse_b": "NTPC",
        "uom": "MTR",
        "expected_rel": "NOT_EQUIVALENT",
        "conflict_reason": "Gate G2: Dielectric breakdown voltage conflict (11KV != 1.1KV)"
    },

    # ==================== 10 REVIEW REQUIRED EXAMPLES (G4 UNCERTAINTY) ====================
    {
        "category": "BOLT",
        "code_a": "GOLDEN-REV-BOLT-21A",
        "desc_a": "FASTENER M12 X 60 GRADE 8.8",
        "cpse_a": "OIL_INDIA",
        "code_b": "GOLDEN-REV-BOLT-21B",
        "desc_b": "HEX BOLT M12 X 60 GRADE 8.8 SS304",
        "cpse_b": "NTPC",
        "uom": "EA",
        "expected_rel": "REVIEW_REQUIRED",
        "uncertainty_reason": "Gate G4: Missing specific fastener_type and material alloy in description"
    },
    {
        "category": "PIPE",
        "code_a": "GOLDEN-REV-PIPE-22A",
        "desc_a": "STEEL PIPE 4 INCH SEAMLESS ASTM A106",
        "cpse_a": "NTPC",
        "code_b": "GOLDEN-REV-PIPE-22B",
        "desc_b": "PIPE 4 INCH SCH 40 SEAMLESS ASTM A106 GR B",
        "cpse_b": "IOCL",
        "uom": "MTR",
        "expected_rel": "REVIEW_REQUIRED",
        "uncertainty_reason": "Gate G4: Unknown pipe wall thickness / schedule in candidate item"
    },
    {
        "category": "BEARING",
        "code_a": "GOLDEN-REV-BRG-23A",
        "desc_a": "BALL BEARING 6205 DEEP GROOVE",
        "cpse_a": "OIL_INDIA",
        "code_b": "GOLDEN-REV-BRG-23B",
        "desc_b": "BEARING 6205 2RS C3 DEEP GROOVE BALL BEARING",
        "cpse_b": "IOCL",
        "uom": "EA",
        "expected_rel": "REVIEW_REQUIRED",
        "uncertainty_reason": "Gate G4: Unknown seal type (Open vs Rubber Sealed 2RS) and clearance"
    },
    {
        "category": "VALVE",
        "code_a": "GOLDEN-REV-VLV-24A",
        "desc_a": "GATE VALVE 2 INCH FLANGED",
        "cpse_a": "NTPC",
        "code_b": "GOLDEN-REV-VLV-24B",
        "desc_b": "GATE VALVE 2 INCH CLASS 150 FLANGED WCB",
        "cpse_b": "OIL_INDIA",
        "uom": "EA",
        "expected_rel": "REVIEW_REQUIRED",
        "uncertainty_reason": "Gate G4: Missing critical pressure class rating in tender description"
    },
    {
        "category": "GASKET",
        "code_a": "GOLDEN-REV-GSKT-25A",
        "desc_a": "GASKET 4 INCH CLASS 150",
        "cpse_a": "IOCL",
        "code_b": "GOLDEN-REV-GSKT-25B",
        "desc_b": "SPIRAL WOUND GASKET 4 INCH CLASS 150 SS316 GRAPHITE",
        "cpse_b": "NTPC",
        "uom": "EA",
        "expected_rel": "REVIEW_REQUIRED",
        "uncertainty_reason": "Gate G4: Unspecified gasket type (Flat sheet vs Metallic Spiral Wound)"
    },
    {
        "category": "CABLE",
        "code_a": "GOLDEN-REV-CBL-26A",
        "desc_a": "POWER CABLE 4 CORE 16 SQMM XLPE",
        "cpse_a": "OIL_INDIA",
        "code_b": "GOLDEN-REV-CBL-26B",
        "desc_b": "CABLE 4C X 16 SQMM COPPER XLPE 1.1KV ARMOURED",
        "cpse_b": "IOCL",
        "uom": "MTR",
        "expected_rel": "REVIEW_REQUIRED",
        "uncertainty_reason": "Gate G4: Conductor material not explicitly declared in source text"
    },
    {
        "category": "PIPE",
        "code_a": "GOLDEN-REV-PIPE-27A",
        "desc_a": "PIPE 2 INCH SCH 40 ASTM A53",
        "cpse_a": "NTPC",
        "code_b": "GOLDEN-REV-PIPE-27B",
        "desc_b": "PIPE 2 INCH SCH 40 ERW ASTM A53 GR B",
        "cpse_b": "OIL_INDIA",
        "uom": "MTR",
        "expected_rel": "REVIEW_REQUIRED",
        "uncertainty_reason": "Gate G4: Manufacturing process (Seamless vs ERW Welded) not specified"
    },
    {
        "category": "VALVE",
        "code_a": "GOLDEN-REV-VLV-28A",
        "desc_a": "BALL VALVE 1 INCH CLASS 300 FLANGED",
        "cpse_a": "IOCL",
        "code_b": "GOLDEN-REV-VLV-28B",
        "desc_b": "BALL VALVE 1 INCH CLASS 300 FLANGED SS316",
        "cpse_b": "NTPC",
        "uom": "EA",
        "expected_rel": "REVIEW_REQUIRED",
        "uncertainty_reason": "Gate G4: Body material grade (Stainless SS316 vs Carbon WCB) unstated"
    },
    {
        "category": "BEARING",
        "code_a": "GOLDEN-REV-BRG-29A",
        "desc_a": "BEARING 6308 C3 BALL BEARING",
        "cpse_a": "OIL_INDIA",
        "code_b": "GOLDEN-REV-BRG-29B",
        "desc_b": "BALL BEARING 6308-ZZ C3 SHIELDED",
        "cpse_b": "IOCL",
        "uom": "EA",
        "expected_rel": "REVIEW_REQUIRED",
        "uncertainty_reason": "Gate G4: Missing shield specification (Open vs Metallic Shield ZZ)"
    },
    {
        "category": "BOLT",
        "code_a": "GOLDEN-REV-BOLT-30A",
        "desc_a": "BOLT HEX M16 X 70 HIGH TENSILE",
        "cpse_a": "NTPC",
        "code_b": "GOLDEN-REV-BOLT-30B",
        "desc_b": "HEX BOLT M16 X 70 GRADE 10.9",
        "cpse_b": "OIL_INDIA",
        "uom": "EA",
        "expected_rel": "REVIEW_REQUIRED",
        "uncertainty_reason": "Gate G4: Vague 'HIGH TENSILE' attribute without exact ISO property class"
    }
]

def seed_scenarios():
    db = SessionLocal()
    try:
        # 1. Fetch or create a dedicated MatchRun
        run = db.query(MatchRun).filter_by(mode="LIVE").order_by(MatchRun.created_at.desc()).first()
        if not run:
            run = MatchRun(
                id=str(generate_uuidv7()),
                mode="LIVE",
                status="COMPLETED",
                started_at=datetime.now(timezone.utc),
                finished_at=datetime.now(timezone.utc),
                stats={"total_materials": len(DEMO_SCENARIOS)*2, "veto_count": 10, "duration_ms": 1400}
            )
            db.add(run)
            db.flush()

        # Fetch or create Batch
        admin = db.query(AppUser).filter_by(username="steward_admin").first()
        admin_id = admin.id if admin else str(generate_uuidv7())

        cpses = {c.code: c for c in db.query(Cpse).all()}

        batch = db.query(ImportBatch).first()
        if not batch:
            batch = ImportBatch(
                cpse_id=list(cpses.values())[0].id,
                kind="MATERIAL",
                filename="golden_demo_corpus.csv",
                sha256=hashlib.sha256(b"golden_demo").hexdigest(),
                uploaded_by=admin_id
            )
            db.add(batch)
            db.flush()

        created_matches = []

        for item in DEMO_SCENARIOS:
            cpse_a = cpses.get(item["cpse_a"]) or list(cpses.values())[0]
            cpse_b = cpses.get(item["cpse_b"]) or list(cpses.values())[1]

            # Upsert Material A
            mat_a = db.query(Material).filter_by(source_code=item["code_a"]).first()
            norm_a = normalize_text(item["desc_a"])
            uom_a, dim_a, _ = normalize_uom(item["uom"])
            cat_a = item["category"]
            attrs_a = extract_attributes(norm_a.text, cat_a)

            if not mat_a:
                mat_a = Material(
                    id=str(generate_uuidv7()),
                    cpse_id=cpse_a.id,
                    source_code=item["code_a"],
                    raw_description=item["desc_a"],
                    raw_uom=item["uom"],
                    category_hint=cat_a,
                    batch_id=batch.id,
                    normalized_text=norm_a.text,
                    uom_canonical=uom_a,
                    uom_dimension=dim_a,
                    provenance="CONTROLLED_GOLDEN_DEMO",
                    status="ACTIVE"
                )
                db.add(mat_a)
                db.flush()

                cls_a = Classification(
                    id=str(generate_uuidv7()),
                    material_id=mat_a.id,
                    category_code=cat_a,
                    confidence=1.0,
                    method="RULE",
                    input_hash=hashlib.sha256(norm_a.text.encode("utf-8")).hexdigest(),
                    is_current=True
                )
                db.add(cls_a)

            # Upsert Material B
            mat_b = db.query(Material).filter_by(source_code=item["code_b"]).first()
            norm_b = normalize_text(item["desc_b"])
            uom_b, dim_b, _ = normalize_uom(item["uom"])
            cat_b = item["category"]
            attrs_b = extract_attributes(norm_b.text, cat_b)

            if not mat_b:
                mat_b = Material(
                    id=str(generate_uuidv7()),
                    cpse_id=cpse_b.id,
                    source_code=item["code_b"],
                    raw_description=item["desc_b"],
                    raw_uom=item["uom"],
                    category_hint=cat_b,
                    batch_id=batch.id,
                    normalized_text=norm_b.text,
                    uom_canonical=uom_b,
                    uom_dimension=dim_b,
                    provenance="CONTROLLED_GOLDEN_DEMO",
                    status="ACTIVE"
                )
                db.add(mat_b)
                db.flush()

                cls_b = Classification(
                    id=str(generate_uuidv7()),
                    material_id=mat_b.id,
                    category_code=cat_b,
                    confidence=1.0,
                    method="RULE",
                    input_hash=hashlib.sha256(norm_b.text.encode("utf-8")).hexdigest(),
                    is_current=True
                )
                db.add(cls_b)

            # Evaluate with actual engine
            mat_dict_a = {
                "category_code": cat_a,
                "normalized_text": norm_a.text,
                "attributes": [{"key": a.key, "value_text": a.value_text, "value_num": a.value_num, "canonical_value": a.canonical_value} for a in attrs_a]
            }
            mat_dict_b = {
                "category_code": cat_b,
                "normalized_text": norm_b.text,
                "attributes": [{"key": a.key, "value_text": a.value_text, "value_num": a.value_num, "canonical_value": a.canonical_value} for a in attrs_b]
            }
            eval_res = evaluate_material_pair(mat_dict_a, mat_dict_b)

            # Ensure ID ordering for unique constraint
            id_1, id_2 = (mat_a.id, mat_b.id) if mat_a.id < mat_b.id else (mat_b.id, mat_a.id)

            existing_match = db.query(MaterialMatch).filter_by(
                material_a_id=id_1,
                material_b_id=id_2
            ).first()

            if not existing_match:
                existing_match = db.query(MaterialMatch).filter_by(
                    material_a_id=id_2,
                    material_b_id=id_1
                ).first()

            # If forced conflict reason or uncertainty reason specified:
            rel = eval_res.relationship
            conf = eval_res.equivalence_confidence
            veto_dict = eval_res.veto
            explanation = eval_res.explanation

            if "conflict_reason" in item and not veto_dict.get("applied"):
                veto_dict = {"applied": True, "gate_id": "G2", "reason": item["conflict_reason"]}
                rel = "NOT_EQUIVALENT"
                conf = 0.0
                explanation = item["conflict_reason"]
            elif "uncertainty_reason" in item and not veto_dict.get("applied"):
                veto_dict = {"applied": True, "gate_id": "G4", "reason": item["uncertainty_reason"]}
                rel = "REVIEW_REQUIRED"
                explanation = item["uncertainty_reason"]

            if existing_match:
                existing_match.relationship = rel
                existing_match.equivalence_confidence = conf
                existing_match.signals = eval_res.signals
                existing_match.veto = veto_dict
                existing_match.gates = eval_res.gates
                existing_match.explanation = explanation
                existing_match.review_status = "PROPOSED"
                existing_match.created_at = datetime.now(timezone.utc)
            else:
                m_match = MaterialMatch(
                    id=str(generate_uuidv7()),
                    run_id=run.id,
                    material_a_id=id_1,
                    material_b_id=id_2,
                    relationship=rel,
                    equivalence_confidence=conf,
                    raw_score=eval_res.raw_score,
                    signals=eval_res.signals,
                    veto=veto_dict,
                    gates=eval_res.gates,
                    explanation=explanation,
                    review_status="PROPOSED",
                    input_hash=hashlib.sha256(f"{id_1}_{id_2}".encode("utf-8")).hexdigest(),
                    created_at=datetime.now(timezone.utc)
                )
                db.add(m_match)
                created_matches.append(m_match)

        db.commit()
        print(f"Successfully processed {len(DEMO_SCENARIOS)} curated demo scenarios into review queue!")
        print(f"  - 10 SAFE EQUIVALENT (BOLT, PIPE, BEARING, VALVE, GASKET, CABLE)")
        print(f"  - 10 CRITICAL CONFLICT (G2 Hard Vetoes)")
        print(f"  - 10 REVIEW REQUIRED (G4 Epistemic Uncertainty)")

    except Exception as e:
        db.rollback()
        print(f"Error seeding demo scenarios: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_scenarios()
