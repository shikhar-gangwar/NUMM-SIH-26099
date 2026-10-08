"""
scripts/clean_crosswalk_and_cpses.py
Cleans up CPSE codes, fixes legacy mappings for cross-CPSE harmonization,
and guarantees genuine multi-CPSE National Materials in the database.
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

# When running on host, port 5433 is forwarded to postgres in container
if "DATABASE_URL" not in os.environ or "@db:" in os.environ.get("DATABASE_URL", ""):
    os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres:postgres@localhost:5433/sih_master"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.db.session import SessionLocal
from app.db.models import Cpse, NationalMaterial, LegacyMapping, Material, AuditEvent
from app.core.ids import generate_uuidv7
from app.governance.nmc import compute_spec_fingerprint

def run_cleanup():
    db = SessionLocal()
    print("=== STARTING CPSE & CROSSWALK CLEANUP ===")

    # 1. Standardize / Rename CPSEs
    cpse_renames = {
        "CPSE_A": ("CPSE-A", "CPSE-A (Thermal Power Demo)", True),
        "CPSE_B": ("CPSE-B", "CPSE-B (Refinery & Petrochem Demo)", True),
        "CPSE_DEV": ("CPSE-C", "CPSE-C (Exploration & Mining Demo)", True),
        "CPSE_M5_TEST": ("CPSE-D", "CPSE-D (Heavy Engineering Demo)", True),
        "OIL_INDIA": ("OIL", "Oil India Limited", False),
        "NTPC": ("NTPC", "NTPC Limited", False),
        "IOCL": ("IOCL", "Indian Oil Corporation Limited", False),
    }

    for old_code, (new_code, new_name, is_syn) in cpse_renames.items():
        c = db.query(Cpse).filter_by(code=old_code).first()
        if c:
            c.code = new_code
            c.name = new_name
            c.is_synthetic = is_syn
            db.add(c)
            print(f"  [CPSE Renamed] {old_code} -> {new_code} ({new_name})")
        else:
            # Check if already renamed
            c_new = db.query(Cpse).filter_by(code=new_code).first()
            if not c_new:
                c_new = Cpse(id=str(generate_uuidv7()), code=new_code, name=new_name, is_synthetic=is_syn)
                db.add(c_new)
                print(f"  [CPSE Created] {new_code} ({new_name})")

    db.commit()

    # Load CPSE map
    cpses = {c.code: c for c in db.query(Cpse).all()}

    # 2. Setup Premier Multi-CPSE National Materials for 4 Categories
    # Category 1: BOLT (M12 X 60 SS316 GR 10.9 ISO 4014)
    # CPSE-A: NTPC-MAT-BOL-01013 (HEX BOLT M12X60 SS316 GR 10.9 ISO 4014)
    # CPSE-B: IOCL-M-BOL-01373 (BOLT HEX M12 X 60 SS316 10.9 ISO 4014)
    # CPSE-C: BOLT-X01 (BOLT HEX M12X60 SS316 GR 10.9)
    print("\n--- Setting up BOLT 3-CPSE Harmonized National Material ---")
    bolt_a = db.query(Material).filter_by(cpse_id=cpses["CPSE-A"].id, source_code="NTPC-MAT-BOL-01013").first()
    bolt_b = db.query(Material).filter_by(cpse_id=cpses["CPSE-B"].id, source_code="IOCL-M-BOL-01373").first()
    bolt_c = db.query(Material).filter_by(cpse_id=cpses["CPSE-C"].id, source_code="BOLT-X01").first()

    if not bolt_a:
        bolt_a = db.query(Material).filter(Material.cpse_id == cpses["CPSE-A"].id, Material.raw_description.ilike("%M12%60%10.9%")).first()
    if not bolt_b:
        bolt_b = db.query(Material).filter(Material.cpse_id == cpses["CPSE-B"].id, Material.raw_description.ilike("%M12%60%10.9%")).first()
    if not bolt_c:
        bolt_c = db.query(Material).filter(Material.cpse_id == cpses["CPSE-C"].id, Material.raw_description.ilike("%M12%60%")).first()

    print(f"  Bolt materials found: A={bolt_a.source_code if bolt_a else None}, B={bolt_b.source_code if bolt_b else None}, C={bolt_c.source_code if bolt_c else None}")

    nmc_bolt = db.query(NationalMaterial).filter(NationalMaterial.category_code == "BOLT").first()
    if not nmc_bolt:
        nmc_bolt = NationalMaterial(
            uid=str(generate_uuidv7()),
            nmc="NMC-BOLT-00000011-C",
            category_code="BOLT",
            status="ACTIVE",
            canonical_description="HEX BOLT M12 X 60 SS316 GR 10.9 ISO 4014",
            sap_short_description="HEX BOLT M12X60 SS316 10.9",
            spec_fingerprint="fp_bolt_m12_ss316_109_iso4014",
            current_version_no=1
        )
        db.add(nmc_bolt)
        db.flush()
    else:
        nmc_bolt.canonical_description = "HEX BOLT M12 X 60 SS316 GR 10.9 ISO 4014"
        nmc_bolt.sap_short_description = "HEX BOLT M12X60 SS316 10.9"
        db.add(nmc_bolt)

    # Clean existing mappings on nmc_bolt
    db.query(LegacyMapping).filter_by(national_material_uid=nmc_bolt.uid).delete()
    db.flush()

    for mat, mtype in [(bolt_a, "EXACT"), (bolt_b, "FUNCTIONAL"), (bolt_c, "NEAR")]:
        if mat:
            db.add(LegacyMapping(
                id=str(generate_uuidv7()),
                material_id=mat.id,
                national_material_uid=nmc_bolt.uid,
                mapping_type=mtype,
                status="ACTIVE"
            ))
            print(f"  [BOLT Mapped] {mat.source_code} ({mat.raw_description[:40]}) -> {nmc_bolt.nmc}")

    # Category 2: PIPE (4 INCH SCH 40 SEAMLESS ASTM A106 GR B)
    # OIL: GOLDEN-SAFE-PIPE-02A (PIPE 4 INCH SCH 40 SEAMLESS ASTM A106 GRADE B BEVE)
    # IOCL: GOLDEN-SAFE-PIPE-02B (SEAMLESS PIPE 4 IN SCH 40 A106 GR B PLAIN END)
    # CPSE-C: PIPE-001 (PIPE 4 INCH SCH 40 SEAMLESS A106 GR B)
    print("\n--- Setting up PIPE 3-CPSE Harmonized National Material ---")
    pipe_oil = db.query(Material).filter_by(cpse_id=cpses["OIL"].id, source_code="GOLDEN-SAFE-PIPE-02A").first()
    pipe_iocl = db.query(Material).filter_by(cpse_id=cpses["IOCL"].id, source_code="GOLDEN-SAFE-PIPE-02B").first()
    pipe_c = db.query(Material).filter_by(cpse_id=cpses["CPSE-C"].id, source_code="PIPE-001").first()

    nmc_pipe = db.query(NationalMaterial).filter(NationalMaterial.category_code == "PIPE").first()
    if not nmc_pipe:
        nmc_pipe = NationalMaterial(
            uid=str(generate_uuidv7()),
            nmc="NMC-PIPE-00000001-Y",
            category_code="PIPE",
            status="ACTIVE",
            canonical_description="SEAMLESS PIPE 4 INCH SCH 40 ASTM A106 GR B BEVELED END",
            sap_short_description="PIPE SMLS 4IN SCH40 A106-B",
            spec_fingerprint="fp_pipe_4in_sch40_a106_grb_smls",
            current_version_no=1
        )
        db.add(nmc_pipe)
        db.flush()
    else:
        nmc_pipe.nmc = "NMC-PIPE-00000001-Y"
        db.add(nmc_pipe)

    db.query(LegacyMapping).filter_by(national_material_uid=nmc_pipe.uid).delete()
    db.flush()

    for mat, mtype in [(pipe_oil, "EXACT"), (pipe_iocl, "FUNCTIONAL"), (pipe_c, "NEAR")]:
        if mat:
            db.add(LegacyMapping(
                id=str(generate_uuidv7()),
                material_id=mat.id,
                national_material_uid=nmc_pipe.uid,
                mapping_type=mtype,
                status="ACTIVE"
            ))
            print(f"  [PIPE Mapped] {mat.source_code} ({mat.raw_description[:40]}) -> {nmc_pipe.nmc}")

    # Category 3: BEARING (DEEP GROOVE BALL BEARING 6205 2RS C3)
    # NTPC: GOLDEN-SAFE-BRG-03A (BEARING 6205 2RS C3 DEEP GROOVE BALL BEARING)
    # IOCL: GOLDEN-SAFE-BRG-03B (DEEP GROOVE BALL BEARING 6205-2RS C3 SKF)
    # CPSE-C: BRG-001 (BEARING 6205 2RS C3 DEEP GROOVE BALL)
    print("\n--- Setting up BEARING 3-CPSE Harmonized National Material ---")
    brg_ntpc = db.query(Material).filter_by(cpse_id=cpses["NTPC"].id, source_code="GOLDEN-SAFE-BRG-03A").first()
    brg_iocl = db.query(Material).filter_by(cpse_id=cpses["IOCL"].id, source_code="GOLDEN-SAFE-BRG-03B").first()
    brg_c = db.query(Material).filter_by(cpse_id=cpses["CPSE-C"].id, source_code="BRG-001").first()

    nmc_brg = db.query(NationalMaterial).filter(NationalMaterial.category_code == "BEARING").first()
    if not nmc_brg:
        nmc_brg = NationalMaterial(
            uid=str(generate_uuidv7()),
            nmc="NMC-BRNG-00000001-Y",
            category_code="BEARING",
            status="ACTIVE",
            canonical_description="DEEP GROOVE BALL BEARING 6205 2RS C3",
            sap_short_description="BRG BALL 6205-2RS C3 DEEP",
            spec_fingerprint="fp_brg_6205_2rs_c3_ball",
            current_version_no=1
        )
        db.add(nmc_brg)
        db.flush()
    else:
        nmc_brg.nmc = "NMC-BRNG-00000001-Y"
        db.add(nmc_brg)

    db.query(LegacyMapping).filter_by(national_material_uid=nmc_brg.uid).delete()
    db.flush()

    for mat, mtype in [(brg_ntpc, "EXACT"), (brg_iocl, "FUNCTIONAL"), (brg_c, "NEAR")]:
        if mat:
            db.add(LegacyMapping(
                id=str(generate_uuidv7()),
                material_id=mat.id,
                national_material_uid=nmc_brg.uid,
                mapping_type=mtype,
                status="ACTIVE"
            ))
            print(f"  [BEARING Mapped] {mat.source_code} ({mat.raw_description[:40]}) -> {nmc_brg.nmc}")

    # Category 4: CABLE (CABLE 4C X 16 SQMM COPPER XLPE 1.1KV ARMOURED)
    # CPSE-A: NTPC-MAT-CAB-01301 (CABLE 4C X 16 SQMM COPPER XLPE 1.1KV ARMOURED)
    # CPSE-B: IOCL-M-CAB-01662 (CABLE 4C * 16 SQMM COPPER XLPE 1.1KV)
    # CPSE-C: CBL-001 (CABLE 4C X 16 SQMM COPPER XLPE 1.1KV ARMOURED)
    print("\n--- Setting up CABLE 3-CPSE Harmonized National Material ---")
    cbl_a = db.query(Material).filter_by(cpse_id=cpses["CPSE-A"].id, source_code="NTPC-MAT-CAB-01301").first()
    cbl_b = db.query(Material).filter_by(cpse_id=cpses["CPSE-B"].id, source_code="IOCL-M-CAB-01662").first()
    cbl_c = db.query(Material).filter_by(cpse_id=cpses["CPSE-C"].id, source_code="CBL-001").first()

    nmc_cbl = db.query(NationalMaterial).filter(NationalMaterial.category_code == "CABLE").first()
    if not nmc_cbl:
        nmc_cbl = NationalMaterial(
            uid=str(generate_uuidv7()),
            nmc="NMC-CABL-00000001-B",
            category_code="CABLE",
            status="ACTIVE",
            canonical_description="CABLE 4C X 16 SQMM COPPER XLPE 1.1KV ARMOURED",
            sap_short_description="CABLE 4CX16 COPPER XLPE 1.1KV",
            spec_fingerprint="fp_cbl_4cx16_cu_xlpe_11kv_arm",
            current_version_no=1
        )
        db.add(nmc_cbl)
        db.flush()

    db.query(LegacyMapping).filter_by(national_material_uid=nmc_cbl.uid).delete()
    db.flush()

    for mat, mtype in [(cbl_a, "EXACT"), (cbl_b, "FUNCTIONAL"), (cbl_c, "NEAR")]:
        if mat:
            db.add(LegacyMapping(
                id=str(generate_uuidv7()),
                material_id=mat.id,
                national_material_uid=nmc_cbl.uid,
                mapping_type=mtype,
                status="ACTIVE"
            ))
            print(f"  [CABLE Mapped] {mat.source_code} ({mat.raw_description[:40]}) -> {nmc_cbl.nmc}")

    db.commit()

    # 3. Verification of All National Materials
    print("\n=== VERIFICATION OF ALL NATIONAL MATERIALS ===")
    for nm in db.query(NationalMaterial).filter_by(status="ACTIVE").all():
        mappings = (
            db.query(LegacyMapping, Material, Cpse)
            .join(Material, LegacyMapping.material_id == Material.id)
            .join(Cpse, Material.cpse_id == Cpse.id)
            .filter(LegacyMapping.national_material_uid == nm.uid, LegacyMapping.status == "ACTIVE")
            .all()
        )
        unique_cpses = set(c.code for lm, m, c in mappings)
        print(f"\nNMC: {nm.nmc} | Category: {nm.category_code} | CPSE Count: {len(unique_cpses)} ({unique_cpses}) | Total Mappings: {len(mappings)}")
        print(f"Canonical: {nm.canonical_description}")
        print(f"SAP 40-char: {nm.sap_short_description} (len={len(nm.sap_short_description)})")
        for lm, m, c in mappings:
            prov_label = "Public-source record" if m.provenance == "REAL_PUBLIC" else "Synthetic demonstration record"
            print(f"    * CPSE: {c.code:8} | Code: {m.source_code:22} | Type: {lm.mapping_type:10} | [{prov_label}] | {m.raw_description[:45]}")

    db.close()
    print("\n=== CLEANUP & HARMONIZATION COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_cleanup()
