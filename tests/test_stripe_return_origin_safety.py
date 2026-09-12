from __future__ import annotations

import pytest
from fastapi import HTTPException

from app import stripe_billing


def test_vercel_requires_https_canonical_origin_for_billing_redirects(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")

    monkeypatch.delenv("VEZMORA_APP_URL", raising=False)
    with pytest.raises(HTTPException) as missing:
        stripe_billing._billing_return_base_url()
    assert missing.value.status_code == 503

    monkeypatch.setenv("VEZMORA_APP_URL", "http://vexmera.example")
    with pytest.raises(HTTPException) as insecure:
        stripe_billing._billing_return_base_url()
    assert insecure.value.status_code == 503

    monkeypatch.setenv("VEZMORA_APP_URL", "https://vexmera.example/")
    assert stripe_billing._billing_return_base_url() == "https://vexmera.example"


def test_local_billing_redirect_keeps_localhost_fallback(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("VEZMORA_APP_URL", raising=False)
    assert stripe_billing._billing_return_base_url() == "http://localhost:8000"


def test_configured_non_vercel_origin_is_trimmed(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv("VEZMORA_APP_URL", "https://local-preview.example///")
    assert stripe_billing._billing_return_base_url() == "https://local-preview.example"
