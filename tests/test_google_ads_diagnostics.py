from __future__ import annotations

import httpx

from app.google_ads_diagnostics import _google_ads_error_summary


def test_google_ads_error_summary_extracts_safe_api_metadata():
    response = httpx.Response(
        403,
        json={
            "error": {
                "status": "PERMISSION_DENIED",
                "message": "Request is not authorized.",
                "details": [
                    {
                        "requestId": "request-123",
                        "errors": [
                            {
                                "errorCode": {
                                    "authorizationError": "DEVELOPER_TOKEN_NOT_APPROVED"
                                },
                                "message": "Developer token is not approved for this account.",
                            }
                        ],
                    }
                ],
            }
        },
    )

    summary = _google_ads_error_summary(response)

    assert summary is not None
    assert "PERMISSION_DENIED" in summary
    assert "authorizationError=DEVELOPER_TOKEN_NOT_APPROVED" in summary
    assert "Developer token is not approved for this account." in summary
    assert "request_id=request-123" in summary


def test_google_ads_error_summary_handles_non_json_response():
    response = httpx.Response(500, content=b"not-json")

    assert _google_ads_error_summary(response) is None


def test_google_ads_error_summary_caps_output_length():
    response = httpx.Response(
        400,
        json={
            "error": {
                "status": "INVALID_ARGUMENT",
                "message": "x" * 2000,
            }
        },
    )

    summary = _google_ads_error_summary(response)

    assert summary is not None
    assert len(summary) <= 900


def test_google_ads_error_summary_redacts_known_secret_values(monkeypatch):
    monkeypatch.setenv("GOOGLE_ADS_DEVELOPER_TOKEN", "dev-secret-123")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "client-secret-456")
    response = httpx.Response(
        403,
        json={
            "error": {
                "status": "PERMISSION_DENIED",
                "message": "developer-token=dev-secret-123 client-secret-456",
                "details": [
                    {
                        "requestId": "request-789",
                        "errors": [
                            {
                                "errorCode": {"authorizationError": "USER_PERMISSION_DENIED"},
                                "message": "Bearer oauth-token-abc access_token=access-123",
                            }
                        ],
                    }
                ],
            }
        },
    )

    summary = _google_ads_error_summary(response)

    assert summary is not None
    assert "dev-secret-123" not in summary
    assert "client-secret-456" not in summary
    assert "oauth-token-abc" not in summary
    assert "access-123" not in summary
    assert summary.count("[REDACTED]") >= 3
    assert "PERMISSION_DENIED" in summary
    assert "request_id=request-789" in summary
