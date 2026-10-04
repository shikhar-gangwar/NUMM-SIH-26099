import os
import uuid
import pandas as pd
import pytest
from fastapi.testclient import TestClient

def test_csv_import_end_to_end(client: TestClient, auth_headers: dict):
    uid = uuid.uuid4().hex[:6]
    csv_content = f"""source_material_code,description,uom,category_hint,manufacturer,part_number
CSV-BOLT-{uid},BOLT HEX M10X50 SS304 GR 8.8 IS 1363,NOS,FASTENERS,UNBRAKO,M10X50-88
CSV-PIPE-{uid},PIPE 4 INCH SCH 40 SEAMLESS A106 GR B,MTR,PIPING,JINDAL,P4-SCH40
CSV-BRG-{uid},BEARING 6205 2RS C3 DEEP GROOVE BALL,EA,BEARINGS,SKF,6205-2RS-C3
CSV-VLV-{uid},GATE VALVE 2 INCH CLASS 150 FLANGED A216 WCB,EA,VALVES,L&T,GV2-150
CSV-GSKT-{uid},SPIRAL WOUND GASKET 4 INCH CLASS 300 SS304,NOS,GASKETS,FLEXITALLIC,SWG4-300
CSV-CBL-{uid},CABLE 4C X 16 SQMM COPPER XLPE 1.1KV ARMOURED,MTR,CABLES,POLYCAB,CBL-4C16
"""
    files = {"file": ("test_import.csv", csv_content.encode("utf-8"), "text/csv")}
    response = client.post(
        "/api/v1/imports/upload",
        files=files,
        headers=auth_headers
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "batch" in data
    assert data["batch"]["filename"] == "test_import.csv"
    assert data["batch"]["total_rows"] == 6
    assert data["batch"]["accepted_rows"] == 6
    batch_id = data["batch"]["id"]

    # Verify batch detail
    detail_res = client.get(f"/api/v1/imports/{batch_id}", headers=auth_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == batch_id

    # Verify batch materials
    mat_res = client.get(f"/api/v1/imports/{batch_id}/materials", headers=auth_headers)
    assert mat_res.status_code == 200
    materials = mat_res.json()
    assert len(materials) == 6
    assert any(m["category_code"] == "BOLT" for m in materials)

def test_xlsx_import_end_to_end(client: TestClient, auth_headers: dict, tmp_path):
    uid = uuid.uuid4().hex[:6]
    df = pd.DataFrame([
        {
            "source_material_code": f"XLS-BOLT-{uid}",
            "description": "HEX BOLT M12 X 60 GRADE 8.8 GALVANIZED",
            "uom": "NOS",
            "category_hint": "FASTENERS",
            "manufacturer": "TATA",
            "part_number": "M12X60"
        },
        {
            "source_material_code": f"XLS-PIPE-{uid}",
            "description": "PIPE 2 INCH SCH 80 STAINLESS STEEL 304 SEAMLESS",
            "uom": "MTR",
            "category_hint": "PIPING",
            "manufacturer": "JINDAL",
            "part_number": "P2-SCH80"
        },
        {
            "source_material_code": f"XLS-BRG-{uid}",
            "description": "BALL BEARING 6308 ZZ C3 HIGH SPEED",
            "uom": "EA",
            "category_hint": "BEARING",
            "manufacturer": "FAG",
            "part_number": "6308-ZZ"
        }
    ])
    excel_path = tmp_path / "test_import.xlsx"
    df.to_excel(excel_path, index=False)

    with open(excel_path, "rb") as f:
        files = {"file": ("test_import.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        response = client.post(
            "/api/v1/imports/upload",
            files=files,
            headers=auth_headers
        )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "batch" in data
    assert data["batch"]["filename"] == "test_import.xlsx"
    assert data["batch"]["total_rows"] == 3
    assert data["batch"]["accepted_rows"] == 3
