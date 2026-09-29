import uuid
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_user_registration_and_login():
    unique_email = f"student_{uuid.uuid4().hex[:8]}@edugenie.ai"
    
    # 1. Register
    reg_payload = {
        "name": "Test Scholar",
        "email": unique_email,
        "password": "securepassword123"
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 200
    reg_json = reg_res.json()
    assert reg_json["success"] is True
    assert "access_token" in reg_json["data"]

    # 2. Login
    login_payload = {
        "email": unique_email,
        "password": "securepassword123"
    }
    login_res = client.post("/api/auth/login", json=login_payload)
    assert login_res.status_code == 200
    login_json = login_res.json()
    assert login_json["success"] is True
    assert login_json["data"]["user"]["email"] == unique_email

def test_invalid_login():
    login_payload = {
        "email": "nonexistent@edugenie.ai",
        "password": "wrongpassword"
    }
    res = client.post("/api/auth/login", json=login_payload)
    assert res.status_code == 401
