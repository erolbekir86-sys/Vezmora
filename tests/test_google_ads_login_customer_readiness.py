from __future__ import annotations

from fastapi.testclient import TestClient

from app import beta_readiness
from app.main import app


def test_beta_readiness_reports_login_customer_id_as_boolean_only(monkeypatch):
    login_customer_id = "9445022492"
    monkeypatch.setenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", login_customer_id)

    snapshot = beta_readiness.beta_safety_snapshot()
    assert snapshot["google_ads_login_customer_id_configured"] is True

    with TestClient(app) as client:
        response = client.get("/health/beta-readiness")

    assert response.status_code == 200
    assert response.json()["google_ads_login_customer_id_configured"] is True
    assert login_customer_id not in response.text


def test_beta_readiness_reports_missing_login_customer_id(monkeypatch):
    monkeypatch.delenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", raising=False)

    snapshot = beta_readiness.beta_safety_snapshot()
    assert snapshot["google_ads_login_customer_id_configured"] is False
