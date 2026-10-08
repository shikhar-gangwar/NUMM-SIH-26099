#!/usr/bin/env python3
"""
Synthetic Material Dataset Generator for National Unified Material Master Framework (SIH 2026 PS 26099).

Generates a deterministic, reproducible corpus across 5 CPSEs and 6 category packs with explicit
ground-truth evaluation pairs, including mandatory AI / matching trap cases.
"""

import os
import json
import random
import argparse
import csv
from pathlib import Path

DEFAULT_SEED = 42

CPSE_PROFILES = [
    {"code": "CPSE_A", "name": "NTPC Style Power CPSE", "prefix": "NTPC-MAT-"},
    {"code": "CPSE_B", "name": "IOCL Style Refinery CPSE", "prefix": "IOCL-M-"},
    {"code": "CPSE_C", "name": "ONGC Style Offshore CPSE", "prefix": "ONGC-P-"},
    {"code": "CPSE_D", "name": "SAIL Style Steel CPSE", "prefix": "SAIL-ST-"},
    {"code": "CPSE_E", "name": "BHEL Style Engineering CPSE", "prefix": "BHEL-E-"}
]

CATEGORIES = ["BOLT", "PIPE", "BEARING", "VALVE", "GASKET", "CABLE"]

# Templates for generating base items per category
BOLT_ITEMS = [
    {"fastener_type": "HEX_BOLT", "dia": 10, "len": 50, "prop": "8.8", "mat": "SS304", "std": "IS 1363"},
    {"fastener_type": "HEX_BOLT", "dia": 12, "len": 60, "prop": "10.9", "mat": "SS316", "std": "ISO 4014"},
    {"fastener_type": "HEX_BOLT", "dia": 16, "len": 70, "prop": "8.8", "mat": "CARBON_STEEL", "std": "DIN 931"},
    {"fastener_type": "STUD_BOLT", "dia": 20, "len": 100, "prop": "A2-70", "mat": "SS304", "std": "ASME B18.31.2"},
    {"fastener_type": "CAP_SCREW", "dia": 8, "len": 30, "prop": "12.9", "mat": "ALLOY_STEEL", "std": "DIN 912"}
]

PIPE_ITEMS = [
    {"spec": "A106_GR_B", "size": "4 IN", "sch": "SCH_40", "mfg": "SEAMLESS", "std": "ASTM A106"},
    {"spec": "A106_GR_B", "size": "4 IN", "sch": "SCH_80", "mfg": "SEAMLESS", "std": "ASTM A106"},
    {"spec": "A53_GR_B", "size": "2 IN", "sch": "SCH_40", "mfg": "ERW", "std": "ASTM A53"},
    {"spec": "API_5L_X52", "size": "6 IN", "sch": "SCH_80", "mfg": "SEAMLESS", "std": "API 5L"},
    {"spec": "SS304", "size": "3 IN", "sch": "SCH_10S", "mfg": "SEAMLESS", "std": "ASTM A312"}
]

BEARING_ITEMS = [
    {"desig": "6205", "type": "DEEP_GROOVE_BALL", "seal": "2RS", "clearance": "C3", "inner": 25, "outer": 52, "width": 15},
    {"desig": "6205", "type": "DEEP_GROOVE_BALL", "seal": "ZZ", "clearance": "C3", "inner": 25, "outer": 52, "width": 15},
    {"desig": "6308", "type": "DEEP_GROOVE_BALL", "seal": "OPEN", "clearance": "CN", "inner": 40, "outer": 90, "width": 23},
    {"desig": "30205", "type": "TAPERED_ROLLER", "seal": "OPEN", "clearance": "CN", "inner": 25, "outer": 52, "width": 16.25},
    {"desig": "22210", "type": "SPHERICAL_ROLLER", "seal": "OPEN", "clearance": "C3", "inner": 50, "outer": 90, "width": 23}
]

VALVE_ITEMS = [
    {"vtype": "GATE", "size": "4 IN", "pclass": "150", "mat": "SS304", "end": "FLANGED"},
    {"vtype": "GATE", "size": "4 IN", "pclass": "300", "mat": "SS304", "end": "FLANGED"},
    {"vtype": "GLOBE", "size": "2 IN", "pclass": "300", "mat": "CARBON_STEEL", "end": "FLANGED"},
    {"vtype": "CHECK", "size": "3 IN", "pclass": "150", "mat": "SS316", "end": "FLANGED"},
    {"vtype": "BALL", "size": "1 IN", "pclass": "800", "mat": "FORGED_STEEL", "end": "SOCKET_WELD"}
]

GASKET_ITEMS = [
    {"gtype": "SPIRAL_WOUND", "size": "4 IN", "pclass": "150", "mat": "SS304"},
    {"gtype": "SPIRAL_WOUND", "size": "4 IN", "pclass": "300", "mat": "SS304"},
    {"gtype": "FLAT_RING", "size": "2 IN", "pclass": "150", "mat": "CAF"},
    {"gtype": "RTJ", "size": "3 IN", "pclass": "600", "mat": "SS316"},
    {"gtype": "FULL_FACE", "size": "6 IN", "pclass": "150", "mat": "EPDM"}
]

CABLE_ITEMS = [
    {"conductor": "COPPER", "sqmm": 16, "cores": 4, "voltage": "1.1KV", "insulation": "XLPE", "armour": "ARMOURED"},
    {"conductor": "COPPER", "sqmm": 16, "cores": 3.5, "voltage": "1.1KV", "insulation": "XLPE", "armour": "ARMOURED"},
    {"conductor": "ALUMINIUM", "sqmm": 95, "cores": 3.5, "voltage": "1.1KV", "insulation": "XLPE", "armour": "ARMOURED"},
    {"conductor": "COPPER", "sqmm": 2.5, "cores": 2, "voltage": "1.1KV", "insulation": "PVC", "armour": "UNARMOURED"},
    {"conductor": "ALUMINIUM", "sqmm": 185, "cores": 3, "voltage": "11KV", "insulation": "XLPE", "armour": "ARMOURED"}
]

def render_bolt_description(item, cpse_style):
    # cpse_style: 0..4
    t = item["fastener_type"].replace("_", " ")
    if cpse_style == 0:
        return f"{t} M{item['dia']}X{item['len']} {item['mat']} GR {item['prop']} {item['std']}"
    elif cpse_style == 1:
        return f"BOLT HEX M{item['dia']} X {item['len']} {item['mat']} {item['prop']} {item['std']}"
    elif cpse_style == 2:
        return f"HEX HEAD BOLT M{item['dia']}X{item['len']} MM {item['mat']} GRADE {item['prop']}"
    elif cpse_style == 3:
        return f"FASTENER {t} M{item['dia']} * {item['len']} {item['mat']} CLASS {item['prop']}"
    else:
        return f"BOLT M{item['dia']}X{item['len']} {item['prop']} {item['mat']}"

def render_pipe_description(item, cpse_style):
    if cpse_style == 0:
        return f"PIPE {item['size']} {item['sch']} {item['mfg']} {item['spec']} {item['std']}"
    elif cpse_style == 1:
        return f"SEAMLESS PIPE {item['size']} {item['sch']} {item['spec']}"
    elif cpse_style == 2:
        return f"PIPE CS {item['size']} {item['sch']} {item['mfg']} SPEC {item['spec']}"
    elif cpse_style == 3:
        return f"{item['size']} PIPE {item['spec']} {item['sch']} {item['mfg']}"
    else:
        return f"TUBING {item['size']} {item['sch']} {item['spec']}"

def render_bearing_description(item, cpse_style):
    if cpse_style == 0:
        return f"BEARING {item['desig']}-{item['seal']} {item['clearance']} ({item['inner']}X{item['outer']}X{item['width']} MM)"
    elif cpse_style == 1:
        return f"BRG DEEP GROOVE BALL {item['desig']} {item['seal']}"
    elif cpse_style == 2:
        return f"BALL BEARING {item['desig']} {item['seal']} {item['clearance']}"
    elif cpse_style == 3:
        return f"BEARING {item['desig']} {item['seal']} CLEARANCE {item['clearance']}"
    else:
        return f"BRG {item['desig']} {item['seal']} ({item['inner']}* {item['outer']}* {item['width']})"

def render_valve_description(item, cpse_style):
    if cpse_style == 0:
        return f"VALVE {item['vtype']} {item['size']} CLASS {item['pclass']} {item['mat']} {item['end']}"
    elif cpse_style == 1:
        return f"{item['vtype']} VALVE {item['size']} CL {item['pclass']} {item['mat']}"
    elif cpse_style == 2:
        return f"VLV {item['vtype']} {item['size']} # {item['pclass']} {item['mat']} {item['end']}"
    elif cpse_style == 3:
        return f"VALVE {item['vtype']} {item['size']} CLASS {item['pclass']} BODY {item['mat']}"
    else:
        return f"FLANGED {item['vtype']} VALVE {item['size']} CL {item['pclass']}"

def render_gasket_description(item, cpse_style):
    g = item['gtype'].replace('_', ' ')
    if cpse_style == 0:
        return f"GASKET {g} {item['size']} CLASS {item['pclass']} {item['mat']}"
    elif cpse_style == 1:
        return f"GSKT {g} {item['size']} CL{item['pclass']} {item['mat']}"
    elif cpse_style == 2:
        return f"SPIRAL WOUND GASKET {item['size']} {item['pclass']} # {item['mat']}"
    else:
        return f"GASKET {item['size']} {item['pclass']} LB {item['mat']}"

def render_cable_description(item, cpse_style):
    c = str(item['cores'])
    if cpse_style == 0:
        return f"CABLE {c}C X {item['sqmm']} SQMM {item['conductor']} {item['insulation']} {item['voltage']} {item['armour']}"
    elif cpse_style == 1:
        return f"CBL {c} CORE {item['sqmm']} MM2 {item['conductor']} {item['voltage']} {item['armour']}"
    elif cpse_style == 2:
        return f"CABLE {c}C * {item['sqmm']} SQMM {item['conductor']} {item['insulation']} {item['voltage']}"
    else:
        return f"POWER CABLE {c}C X {item['sqmm']} SQMM {item['conductor']} {item['voltage']}"

def generate_synthetic_dataset(seed: int = DEFAULT_SEED, output_dir: str = "data/synthetic"):
    random.seed(seed)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    materials_list = []
    procurement_list = []
    ground_truth_pairs = []

    m_counter = 1000

    # 1. Generate base canonical universe
    # Generate ~350 unique canonical items rendered across 5 CPSEs -> ~1,500 total CPSE materials
    for cpse_idx, cpse in enumerate(CPSE_PROFILES):
        cpse_code = cpse["code"]
        
        for category in CATEGORIES:
            if category == "BOLT":
                base_items = BOLT_ITEMS
            elif category == "PIPE":
                base_items = PIPE_ITEMS
            elif category == "BEARING":
                base_items = BEARING_ITEMS
            elif category == "VALVE":
                base_items = VALVE_ITEMS
            elif category == "GASKET":
                base_items = GASKET_ITEMS
            else:
                base_items = CABLE_ITEMS

            for b_idx, base_item in enumerate(base_items):
                # Generate 12-15 variations per base item across CPSEs
                for var_idx in range(12):
                    m_counter += 1
                    mat_code = f"{cpse['prefix']}{category[:3]}-{m_counter:05d}"

                    if category == "BOLT":
                        raw_desc = render_bolt_description(base_item, (cpse_idx + var_idx) % 5)
                    elif category == "PIPE":
                        raw_desc = render_pipe_description(base_item, (cpse_idx + var_idx) % 5)
                    elif category == "BEARING":
                        raw_desc = render_bearing_description(base_item, (cpse_idx + var_idx) % 5)
                    elif category == "VALVE":
                        raw_desc = render_valve_description(base_item, (cpse_idx + var_idx) % 5)
                    elif category == "GASKET":
                        raw_desc = render_gasket_description(base_item, (cpse_idx + var_idx) % 5)
                    else:
                        raw_desc = render_cable_description(base_item, (cpse_idx + var_idx) % 5)

                    uom = random.choice(["NOS", "EA", "PC", "SET", "MTR", "KG"])
                    mfr = random.choice(["UNBRAKO", "TATA", "SKF", "FAG", "L&T", "HAVELS", "GENERIC"])
                    part_num = f"PN-{category[:3]}-{b_idx:03d}"

                    materials_list.append({
                        "id": f"mat-{cpse_code.lower()}-{m_counter}",
                        "cpse_code": cpse_code,
                        "source_material_code": mat_code,
                        "raw_description": raw_desc,
                        "raw_uom": uom,
                        "manufacturer": mfr,
                        "part_number": part_num,
                        "category_hint": category,
                        "is_synthetic": True,
                        "canonical_base_id": f"canon-{category}-{b_idx}"
                    })

                    # Procurement mock record
                    procurement_list.append({
                        "cpse_code": cpse_code,
                        "source_material_code": mat_code,
                        "unit_price": round(random.uniform(50.0, 4500.0), 2),
                        "currency": "INR",
                        "quantity": random.randint(10, 5000),
                        "purchase_date": f"2026-0{random.randint(1,9)}-{random.randint(10,28)}"
                    })

    # 2. Add Mandatory AI / Matching Trap Pairs with Explicit Ground Truth Labels
    trap_pairs_data = [
        # 1. TRUE EQUIVALENT
        {
            "id": "trap-01-true-equiv",
            "mat_a": {
                "id": "mat-eq-01a", "cpse_code": "CPSE_A", "source_material_code": "CPSE_A-BOLT-001",
                "raw_description": "HEX BOLT M12 X 60 SS316 10.9", "raw_uom": "NOS", "category_hint": "BOLT"
            },
            "mat_b": {
                "id": "mat-eq-01b", "cpse_code": "CPSE_B", "source_material_code": "CPSE_B-BOLT-001",
                "raw_description": "BOLT HEX M12X60 SS 316 GR10.9", "raw_uom": "EA", "category_hint": "BOLT"
            },
            "expected_relationship": "FUNCTIONALLY_EQUIVALENT",
            "is_true_equivalent": True,
            "description": "Same technical material described differently across CPSEs"
        },
        # 2. SEMANTICALLY SIMILAR BUT TECHNICALLY DIFFERENT (VETO TRAP: 8.8 vs 10.9)
        {
            "id": "trap-02-veto-88-109",
            "mat_a": {
                "id": "mat-v88-01a", "cpse_code": "CPSE_A", "source_material_code": "CPSE_A-BOLT-002",
                "raw_description": "HEX BOLT M12 X 60 SS316 8.8", "raw_uom": "NOS", "category_hint": "BOLT"
            },
            "mat_b": {
                "id": "mat-v88-01b", "cpse_code": "CPSE_B", "source_material_code": "CPSE_B-BOLT-002",
                "raw_description": "HEX BOLT M12 X 60 SS316 10.9", "raw_uom": "NOS", "category_hint": "BOLT"
            },
            "expected_relationship": "NOT_EQUIVALENT",
            "is_88_109_trap": True,
            "simulated_semantic_score": 0.94,
            "description": "8.8 vs 10.9 property class conflict must trigger VETO gate"
        },
        # 3. UNKNOWN / INSUFFICIENT INFORMATION
        {
            "id": "trap-03-unknown-missing-grade",
            "mat_a": {
                "id": "mat-unk-01a", "cpse_code": "CPSE_A", "source_material_code": "CPSE_A-BOLT-003",
                "raw_description": "HEX BOLT M12 X 60 SS", "raw_uom": "NOS", "category_hint": "BOLT"
            },
            "mat_b": {
                "id": "mat-unk-01b", "cpse_code": "CPSE_B", "source_material_code": "CPSE_B-BOLT-003",
                "raw_description": "HEX BOLT M12 X 60 SS316 10.9", "raw_uom": "NOS", "category_hint": "BOLT"
            },
            "expected_relationship": "REVIEW_REQUIRED",
            "is_unknown_trap": True,
            "description": "Missing property grade requires human review"
        },
        # 4. COMPATIBLE (Standard Equivalence)
        {
            "id": "trap-04-compatible-standard",
            "mat_a": {
                "id": "mat-comp-01a", "cpse_code": "CPSE_A", "source_material_code": "CPSE_A-BOLT-004",
                "raw_description": "HEX BOLT M10 X 50 SS304 GR 8.8 IS 1363", "raw_uom": "NOS", "category_hint": "BOLT"
            },
            "mat_b": {
                "id": "mat-comp-01b", "cpse_code": "CPSE_C", "source_material_code": "CPSE_C-BOLT-004",
                "raw_description": "HEXAGON HEAD BOLT M10 X 50 STAINLESS STEEL 304 GRADE 8.8 ISO 4016", "raw_uom": "EA", "category_hint": "BOLT"
            },
            "expected_relationship": "FUNCTIONALLY_EQUIVALENT",
            "description": "Equivalent standards (IS 1363 vs ISO 4016)"
        },
        # 5. RELATED (Variant axis difference: Length 50 vs 60)
        {
            "id": "trap-05-related-length",
            "mat_a": {
                "id": "mat-rel-01a", "cpse_code": "CPSE_A", "source_material_code": "CPSE_A-BOLT-005",
                "raw_description": "HEX BOLT M12 X 50 SS316 10.9", "raw_uom": "NOS", "category_hint": "BOLT"
            },
            "mat_b": {
                "id": "mat-rel-01b", "cpse_code": "CPSE_B", "source_material_code": "CPSE_B-BOLT-005",
                "raw_description": "HEX BOLT M12 X 60 SS316 10.9", "raw_uom": "NOS", "category_hint": "BOLT"
            },
            "expected_relationship": "RELATED",
            "description": "Same family, variant axis (length) differs"
        },
        # 6. FALSE SEMANTIC MATCHES across categories
        # 6a. Pipe Sch 40 vs Sch 80
        {
            "id": "trap-06a-pipe-sch",
            "mat_a": {
                "id": "mat-sem-pipe-a", "cpse_code": "CPSE_A", "source_material_code": "CPSE_A-PIPE-001",
                "raw_description": "PIPE 4 IN SCH 40 SEAMLESS A106 GR B", "raw_uom": "MTR", "category_hint": "PIPE"
            },
            "mat_b": {
                "id": "mat-sem-pipe-b", "cpse_code": "CPSE_B", "source_material_code": "CPSE_B-PIPE-001",
                "raw_description": "PIPE 4 IN SCH 80 SEAMLESS A106 GR B", "raw_uom": "MTR", "category_hint": "PIPE"
            },
            "expected_relationship": "NOT_EQUIVALENT",
            "is_semantic_trap": True,
            "simulated_semantic_score": 0.95,
            "description": "Pipe Sch 40 vs Sch 80 thickness conflict"
        },
        # 6b. Bearing 6205-2RS vs 6205-ZZ
        {
            "id": "trap-06b-brg-seal",
            "mat_a": {
                "id": "mat-sem-brg-a", "cpse_code": "CPSE_A", "source_material_code": "CPSE_A-BRG-001",
                "raw_description": "BEARING 6205-2RS C3", "raw_uom": "NOS", "category_hint": "BEARING"
            },
            "mat_b": {
                "id": "mat-sem-brg-b", "cpse_code": "CPSE_B", "source_material_code": "CPSE_B-BRG-001",
                "raw_description": "BEARING 6205-ZZ C3", "raw_uom": "NOS", "category_hint": "BEARING"
            },
            "expected_relationship": "NOT_EQUIVALENT",
            "is_semantic_trap": True,
            "simulated_semantic_score": 0.93,
            "description": "Bearing rubber seal (2RS) vs steel shield (ZZ) conflict"
        },
        # 6c. Valve Class 150 vs Class 300
        {
            "id": "trap-06c-vlv-class",
            "mat_a": {
                "id": "mat-sem-vlv-a", "cpse_code": "CPSE_A", "source_material_code": "CPSE_A-VLV-001",
                "raw_description": "VALVE GATE 4 IN CLASS 150 SS304 FLANGED", "raw_uom": "NOS", "category_hint": "VALVE"
            },
            "mat_b": {
                "id": "mat-sem-vlv-b", "cpse_code": "CPSE_B", "source_material_code": "CPSE_B-VLV-001",
                "raw_description": "VALVE GATE 4 IN CLASS 300 SS304 FLANGED", "raw_uom": "NOS", "category_hint": "VALVE"
            },
            "expected_relationship": "NOT_EQUIVALENT",
            "is_semantic_trap": True,
            "simulated_semantic_score": 0.96,
            "description": "Valve Class 150 vs Class 300 pressure rating conflict"
        },
        # 6d. Cable 4C vs 3.5C
        {
            "id": "trap-06d-cbl-cores",
            "mat_a": {
                "id": "mat-sem-cbl-a", "cpse_code": "CPSE_A", "source_material_code": "CPSE_A-CBL-001",
                "raw_description": "CABLE 4C X 16 SQMM COPPER XLPE 1.1KV ARMOURED", "raw_uom": "MTR", "category_hint": "CABLE"
            },
            "mat_b": {
                "id": "mat-sem-cbl-b", "cpse_code": "CPSE_B", "source_material_code": "CPSE_B-CBL-001",
                "raw_description": "CABLE 3.5C X 16 SQMM COPPER XLPE 1.1KV ARMOURED", "raw_uom": "MTR", "category_hint": "CABLE"
            },
            "expected_relationship": "RELATED",
            "is_semantic_trap": True,
            "simulated_semantic_score": 0.95,
            "description": "Cable 4 cores vs 3.5 cores variant axis"
        }
    ]

    # Save CPSE materials files
    for cpse in CPSE_PROFILES:
        cpse_code = cpse["code"]
        cpse_mats = [m for m in materials_list if m["cpse_code"] == cpse_code]
        csv_file = out_path / f"{cpse_code}_materials.csv"
        fieldnames = ["source_material_code", "raw_description", "raw_uom", "manufacturer", "part_number", "category_hint"]
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in cpse_mats:
                writer.writerow({k: row[k] for k in fieldnames})

    # Save all synthetic materials CSV
    all_csv_file = out_path / "all_synthetic_materials.csv"
    all_fieldnames = ["cpse_code", "source_material_code", "raw_description", "raw_uom", "manufacturer", "part_number", "category_hint"]
    with open(all_csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_fieldnames)
        writer.writeheader()
        for row in materials_list:
            writer.writerow({k: row[k] for k in all_fieldnames})

    # Save Ground Truth Pairs JSON
    gt_file = out_path / "ground_truth_pairs.json"
    with open(gt_file, "w", encoding="utf-8") as f:
        json.dump(trap_pairs_data, f, indent=2)

    print(f"Generated {len(materials_list)} synthetic materials across {len(CPSE_PROFILES)} CPSEs.")
    print(f"Generated {len(trap_pairs_data)} ground-truth evaluation pairs in {gt_file}.")
    return len(materials_list), len(trap_pairs_data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic dataset for SIH National Material Master")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed for reproducibility")
    parser.add_argument("--outdir", type=str, default="data/synthetic", help="Output directory")
    args = parser.parse_args()
    generate_synthetic_dataset(seed=args.seed, output_dir=args.outdir)
