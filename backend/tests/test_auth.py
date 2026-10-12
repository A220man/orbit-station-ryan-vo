import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_demo_mode_auth_bypass():
    # In demo mode, requests without auth succeed as operator/viewer
    res = client.get("/api/operators")
    assert res.status_code == 200

def test_role_rejection_for_admin_endpoint():
    # Admin endpoint should reject viewer role
    headers = {"Authorization": "Bearer viewer-token"}
    res = client.get("/api/audit-logs", headers=headers)
    assert res.status_code == 403

def test_admin_role_access():
    headers = {"Authorization": "Bearer admin-token"}
    res = client.get("/api/audit-logs", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_unauthenticated_rejection_in_prod_mode(monkeypatch):
    monkeypatch.setattr(settings, "demo_mode", False)
    res = client.get("/api/operators")
    assert res.status_code == 401
    assert "Missing authorization header" in res.json()["detail"]
