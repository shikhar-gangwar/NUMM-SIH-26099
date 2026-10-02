from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login_invalid_credentials():
    response = client.post("/api/v1/auth/login", json={
        "username": "wrong_user",
        "password": "wrong_password"
    })
    assert response.status_code == 401

def test_meta_version():
    response = client.get("/api/v1/meta/version")
    assert response.status_code == 200
    data = response.json()
    assert "app_version" in data
    assert "llm_badge" in data
