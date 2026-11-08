from __future__ import annotations

import asyncio
import json
from urllib.parse import parse_qs, urlencode, urlsplit

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import connectors, store, tiktok_connector as tiktok
from app.main import app


def configured(monkeypatch):
    values = {
        "VEZMORA_APP_URL": "https://vexmera.com", "VERCEL_ENV": "production",
        "TIKTOK_APP_ID": "1234", "TIKTOK_APP_SECRET": "test-only-app-secret",
        "TIKTOK_REDIRECT_URI": "https://vexmera.com/api/connectors/tiktok/callback",
        "TIKTOK_ADS_API_APPROVED": "true",
    }
    values["TIKTOK_AUTHORIZATION_URL"] = "https://business-api.tiktok.com/portal/auth?" + urlencode({
        "app_id": values["TIKTOK_APP_ID"], "redirect_uri": values["TIKTOK_REDIRECT_URI"],
    })
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    return values


def transport(monkeypatch, handler):
    real_client = httpx.AsyncClient

    def factory(**kwargs):
        assert kwargs["follow_redirects"] is False
        return real_client(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(tiktok.httpx, "AsyncClient", factory)


def connected(monkeypatch, advertiser="111"):
    monkeypatch.setattr(connectors, "get_connector", lambda *args, **kwargs: {
        "status": "connected", "secret_blob": "encrypted",
        "metadata": {"advertiser_id": advertiser},
    })
    monkeypatch.setattr(connectors, "decrypt_json", lambda _: {
        "access_token": "test-access-token", "advertiser_ids": ["111"],
    })


def test_missing_configuration_and_unconfirmed_approval_fail_closed(monkeypatch):
    configured(monkeypatch)
    monkeypatch.setenv("TIKTOK_ADS_API_APPROVED", "false")
    with pytest.raises(HTTPException) as exc:
        tiktok.tiktok_authorization_url(1, 2)
    assert exc.value.status_code == 503
    monkeypatch.setenv("TIKTOK_APP_SECRET", "   ")
    assert connectors.connector_readiness()["tiktok"]["configured"] is False


def test_authorization_uses_portal_url_and_fresh_workspace_bound_state(monkeypatch):
    values = configured(monkeypatch)
    states = []
    monkeypatch.setattr(connectors, "save_oauth_state", lambda *args: states.append(args))
    urls = [tiktok.tiktok_authorization_url(7, 9) for _ in range(2)]
    first = parse_qs(urlsplit(urls[0]).query)
    assert states[0][1:] == (9, 7, "tiktok")
    assert first["redirect_uri"] == [values["TIKTOK_REDIRECT_URI"]]
    assert first["state"] != parse_qs(urlsplit(urls[1]).query)["state"]
    assert "scope" not in first
    assert values["TIKTOK_APP_SECRET"] not in urls[0]


@pytest.mark.parametrize("value", [
    "https://attacker.test/portal/auth?app_id=1234",
    "https://business-api.tiktok.com.attacker.test/portal/auth",
    "https://business-api.tiktok.com/portal/auth?app_id=other&redirect_uri=wrong",
    "http://business-api.tiktok.com/portal/auth",
])
def test_untrusted_or_mismatched_authorization_url_is_rejected(monkeypatch, value):
    configured(monkeypatch)
    monkeypatch.setenv("TIKTOK_AUTHORIZATION_URL", value)
    monkeypatch.setattr(connectors, "save_oauth_state", lambda *args: pytest.fail("No state may be saved"))
    with pytest.raises(HTTPException) as exc:
        tiktok.tiktok_authorization_url(1, 2)
    assert exc.value.status_code == 503


def test_callback_encrypts_only_needed_credentials_and_preserves_selected_account(monkeypatch):
    configured(monkeypatch)
    monkeypatch.setattr(connectors, "consume_oauth_state", lambda state, provider: {"workspace_id": 7})
    monkeypatch.setattr(connectors, "get_connector", lambda *args: {"metadata": {"advertiser_id": "222"}})
    monkeypatch.setattr(connectors, "encrypt_json", lambda value: "encrypted:" + json.dumps(value))
    saved = []
    monkeypatch.setattr(connectors, "save_connector", lambda *args: saved.append(args))

    def handler(request):
        assert request.method == "POST"
        assert str(request.url) == tiktok.API_BASE + "/oauth2/access_token/"
        assert json.loads(request.content)["auth_code"] == "test-code"
        return httpx.Response(200, json={"code": 0, "data": {
            "access_token": "private-test-token", "advertiser_ids": ["111", "222"],
            "unneeded_profile": "must-not-persist",
        }})

    transport(monkeypatch, handler)
    result = asyncio.run(tiktok.tiktok_callback("test-code", "valid-state"))
    assert result == {"ok": True, "provider": "tiktok", "workspace_id": 7}
    assert saved[0][3] == "222"
    assert "private-test-token" in saved[0][5]
    assert "must-not-persist" not in saved[0][5]
    assert "private-test-token" not in json.dumps(saved[0][6])


def test_expired_state_never_calls_provider(monkeypatch):
    configured(monkeypatch)
    monkeypatch.setattr(connectors, "consume_oauth_state", lambda *args: None)
    monkeypatch.setattr(tiktok.httpx, "AsyncClient", lambda **kwargs: pytest.fail("No provider request"))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(tiktok.tiktok_callback("test-code", "expired"))
    assert exc.value.status_code == 400


def report_page(day, campaign="456", currency="USD", spend="10.50", page=1, total=1):
    return {"code": 0, "data": {"list": [{
        "dimensions": {"campaign_id": campaign, "stat_time_day": day},
        "metrics": {"campaign_name": "Test", "currency": currency, "spend": spend, "impressions": "100", "clicks": "5"},
    }], "page_info": {"page": page, "total_page": total}, "extra_info": {}}}


def test_reporting_collects_pages_and_keeps_currencies_out_of_workspace_kpis(monkeypatch):
    configured(monkeypatch)
    connected(monkeypatch)
    day = connectors._date_range(7)[1]
    requests = []
    saved = []
    monkeypatch.setattr(connectors, "update_connector_metadata", lambda *args: saved.append(args))
    monkeypatch.setattr(connectors, "upsert_kpi", lambda *args: pytest.fail("Preview must not affect KPIs"))
    monkeypatch.setattr(connectors, "upsert_campaign_metric", lambda *args: pytest.fail("Preview must not affect reporting history"))

    def handler(request):
        assert str(request.url) == tiktok.API_BASE + "/report/integrated/get/"
        body = json.loads(request.content)
        requests.append(body)
        assert request.headers["Access-Token"] == "test-access-token"
        page = body["page"]
        return httpx.Response(200, json=report_page(day, campaign=str(page), currency="USD" if page == 1 else "EUR", page=page, total=2))

    transport(monkeypatch, handler)
    result = asyncio.run(tiktok.sync_tiktok(7, 90))
    assert len(requests) == 2
    assert requests[0]["advertiser_ids"] == ["111"]
    assert "30 days" in " ".join(result["warnings"])
    assert result["report_rows"] == 2 and result["preview_only"] is True
    assert result["totals_by_currency"]["USD"]["spend"] == 10.5
    assert result["totals_by_currency"]["EUR"]["spend"] == 10.5
    assert len(saved) == 1
    assert "test-access-token" not in json.dumps(saved)


@pytest.mark.parametrize("case", ["http-error", "provider-error", "second-page-error", "duplicate", "bad-metric", "too-many-pages"])
def test_failed_or_partial_report_does_not_replace_previous_report(monkeypatch, case):
    configured(monkeypatch)
    connected(monkeypatch)
    monkeypatch.setattr(connectors, "update_connector_metadata", lambda *args: pytest.fail("Previous report must remain"))
    day = connectors._date_range(7)[1]

    def handler(request):
        page = json.loads(request.content)["page"]
        if case == "http-error" or (case == "second-page-error" and page == 2):
            return httpx.Response(403, json={"secret": "do-not-expose"})
        if case == "provider-error":
            return httpx.Response(200, json={"code": 40000, "message": "private-test-token"})
        payload = report_page(day, spend="NaN" if case == "bad-metric" else "10", page=page, total=21 if case == "too-many-pages" else 2)
        return httpx.Response(200, json=payload)

    transport(monkeypatch, handler)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(tiktok.sync_tiktok(7))
    assert exc.value.status_code in {409, 502}
    assert "private-test-token" not in str(exc.value.detail)


def test_account_must_belong_to_oauth_grant(monkeypatch):
    configured(monkeypatch)
    connected(monkeypatch, advertiser="999")
    monkeypatch.setattr(tiktok.httpx, "AsyncClient", lambda **kwargs: pytest.fail("No provider request"))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(tiktok.sync_tiktok(7))
    assert exc.value.status_code == 409


@pytest.mark.parametrize("query", [
    {"state": "bad state", "auth_code": "test"},
    {"state": "valid-state", "auth_code": "x" * 4097},
    [("state", "one"), ("state", "two"), ("auth_code", "test")],
])
def test_tiktok_callback_input_guard_runs_before_provider_work(query):
    with TestClient(app) as client:
        response = client.get("/api/connectors/tiktok/callback", params=query)
    assert response.status_code == 400
    assert response.headers["cache-control"] == "no-store"


def test_routes_require_login_and_owner_can_disconnect_without_losing_history(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "tiktok.db")
    monkeypatch.setenv("VEZMORA_SECRET_KEY", "local-test-key")
    store.init_db()
    with TestClient(app) as client:
        assert client.get("/api/connectors/tiktok/start?workspace_id=1").status_code == 401
        registration = client.post("/api/auth/register", json={"email": "tiktok-test@example.com", "password": "verysecure123", "workspace_name": "TikTok Test"})
        assert registration.status_code == 200
        workspace_id = registration.json()["workspace_id"]
        store.save_connector(workspace_id, "tiktok", "connected", "111", "TikTok Ads", connectors.encrypt_json({"access_token": "test-token"}), {"last_sync": {"report_rows": 2}})
        response = client.post(f"/api/connectors/tiktok/disconnect?workspace_id={workspace_id}")
        assert response.status_code == 200
        assert response.json()["historical_data_retained"] is True
        assert store.get_connector(workspace_id, "tiktok", include_secret=True)["secret_blob"] is None
