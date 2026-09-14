from __future__ import annotations

import pytest
from fastapi import HTTPException

from app import stripe_billing


def test_vercel_requires_plain_https_canonical_origin_for_billing_redirects(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")

    invalid_values = [
        None,
        "http://vexmera.example",
        "https://user:secret@vexmera.example",
        "https://vexmera.example/app",
        "https://vexmera.example?next=private",
        "https://vexmera.example#billing",
    ]

    for value in invalid_values:
        if value is None:
            monkeypatch.delenv("VEZMORA_APP_URL", raising=False)
        else:
            monkeypatch.setenv("VEZMORA_APP_URL", value)
        with pytest.raises(HTTPException) as error:
            stripe_billing._billing_return_base_url()
        assert error.value.status_code == 503

    monkeypatch.setenv("VEZMORA_APP_URL", "https://vexmera.example/")
    assert stripe_billing._billing_return_base_url() == "https://vexmera.example"


def test_local_billing_redirect_keeps_localhost_fallback(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("VEZMORA_APP_URL", raising=False)
    assert stripe_billing._billing_return_base_url() == "http://localhost:8000"


def test_configured_non_vercel_origin_keeps_existing_trailing_slash_normalization(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv("VEZMORA_APP_URL", "https://local-preview.example///")
    assert stripe_billing._billing_return_base_url() == "https://local-preview.example"
