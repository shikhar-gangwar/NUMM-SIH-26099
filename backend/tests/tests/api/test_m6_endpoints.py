import pytest
from fastapi.testclient import TestClient

def test_crosswalk_export_endpoint(client: TestClient, auth_headers: dict):
    response = client.get("/api/v1/exports/crosswalk.csv", headers=auth_headers)
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "NMC,National_UID,CPSE_Code" in response.text

def test_procurement_analytics_endpoint(client: TestClient, auth_headers: dict):
    response = client.get("/api/v1/analytics/procurement", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "cpse_sharing_nmc_count" in data
    assert "duplicate_materials_count" in data
    assert "top_consolidation_opportunities" in data
    assert "demonstration_notes" in data

def test_materials_listing_endpoint(client: TestClient, auth_headers: dict):
    response = client.get("/api/v1/materials?page=1&page_size=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

