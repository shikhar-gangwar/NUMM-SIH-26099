import pytest
from app.db.models import NationalMaterial, Cpse, Material, LegacyMapping
from app.core.ids import generate_uuidv7

def test_mock_sap_integration_flow(client, auth_headers, db_session):
    # 1. Create test National Material with a long description (> 40 chars)
    nat_mat = NationalMaterial(
        uid=str(generate_uuidv7()),
        nmc="NMC-BOLT-00000099-Z",
        canonical_description="HEXAGON HEAD BOLT M16 X 75MM HIGH TENSILE GRADE 8.8 GALVANIZED FINISH",
        sap_short_description="HEX BOLT M16X75 HT 8.8 GALV",
        category_code="BOLT",
        spec_fingerprint="dummy_fp_sap_test_99",
        status="ACTIVE"
    )
    db_session.add(nat_mat)
    db_session.commit()


    # 2. Test GET /api/v1/integration/sap/status
    res_status = client.get("/api/v1/integration/sap/status", headers=auth_headers)
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data["adapter"] == "MOCK_SAP_S4HANA"
    assert status_data["is_mock"] is True
    assert status_data["description_limit"] == 40

    # 3. Test POST /api/v1/integration/sap/sync
    res_sync = client.post("/api/v1/integration/sap/sync", headers=auth_headers)
    assert res_sync.status_code == 200
    sync_data = res_sync.json()
    assert sync_data["status"] == "COMPLETED"
    assert sync_data["is_mock"] is True
    assert sync_data["records_exported"] >= 1
    assert "sync_id" in sync_data

    # 4. Test GET /api/v1/integration/sap/materials
    res_mats = client.get("/api/v1/integration/sap/materials", headers=auth_headers)
    assert res_mats.status_code == 200
    mats_list = res_mats.json()
    assert len(mats_list) >= 1

    # Verify 40-character constraint enforcement on all items
    for item in mats_list:
        assert len(item["product_description"]) <= 40, f"Exceeded 40 chars: {item['product_description']}"
        assert "MATNR" in item["payload"]["HEADER"]
        assert item["payload"]["IS_MOCK"] is True

def test_saps4_adapter_contract():
    from app.integration.sap import SAPS4Adapter
    adapter = SAPS4Adapter()
    health = adapter.health_check()
    assert health["adapter"] == "SAP_S4HANA_ODATA_V2"
    assert health["is_mock"] is False
    assert health["status"] == "UNCONFIGURED_CREDENTIALS_REQUIRED"

    payload = adapter.transform_nmc_to_product_payload(
        nmc="NMC-BOLT-00000042-X",
        canonical_desc="HEX BOLT M12 X 60 GRADE 8.8 GALVANIZED FINISH WITH ISO 4014 SPECIFICATION",
        uom="EA",
        category="BOLT"
    )
    assert payload["Product"] == "NMCBOLT00000042X"
    assert len(payload["to_Description"][0]["ProductDescription"]) <= 40
    assert payload["ProductGroup"] == "BOLT"

