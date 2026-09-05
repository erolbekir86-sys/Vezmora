from __future__ import annotations

from app.http_error_safety import sanitize_http_detail


def test_http_error_safety_redacts_meta_and_generic_token_patterns(monkeypatch):
    monkeypatch.setenv("META_APP_SECRET", "meta-secret-123")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "google-secret-456")

    detail = {
        "message": "Meta failed with access_token=meta-access-abc and meta-secret-123",
        "nested": [
            "Bearer bearer-token-xyz",
            "client_secret=inline-client-secret",
            "google-secret-456",
        ],
        "code": 190,
    }

    sanitized = sanitize_http_detail(detail)
    rendered = str(sanitized)

    assert "meta-access-abc" not in rendered
    assert "meta-secret-123" not in rendered
    assert "bearer-token-xyz" not in rendered
    assert "inline-client-secret" not in rendered
    assert "google-secret-456" not in rendered
    assert sanitized["code"] == 190
    assert rendered.count("[REDACTED]") >= 5


def test_http_error_safety_preserves_actionable_non_secret_meta_context():
    detail = {
        "message": "Meta ad account lookup failed: Unsupported get request",
        "meta_code": 100,
        "meta_subcode": 33,
    }

    assert sanitize_http_detail(detail) == detail
