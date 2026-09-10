from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_vercel_health_is_minimal_and_does_not_expose_runtime_configuration(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "service": "vexmera",
        "version": "0.6.1",
    }

    serialized = response.text.lower()
    for forbidden in (
        "api_key_configured",
        "oauth_secret_configured",
        "stripe_configured",
        "smtp_configured",
        "storage_backend",
        "data_path",
        "scheduler_enabled",
        "worker_enabled",
    ):
        assert forbidden not in serialized


def test_local_health_keeps_detailed_operator_diagnostics(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["service"] == "vezmora"
    assert "storage_backend" in payload
    assert "data_path" in payload
