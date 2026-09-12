import pytest
from fastapi import HTTPException

from app import stripe_billing


class FakeStripeClient:
    def __init__(self):
        self.calls: list[tuple[bytes, str, str]] = []

    def construct_event(self, payload: bytes, signature: str, secret: str):
        self.calls.append((payload, signature, secret))
        return {"id": "evt_test", "type": "invoice.payment_failed", "data": {"object": {}}}


def test_oversized_webhook_is_rejected_before_stripe_client_or_secret_lookup(monkeypatch):
    monkeypatch.setattr(stripe_billing, "MAX_WEBHOOK_PAYLOAD_BYTES", 8)

    def unexpected_client():
        raise AssertionError("oversized payload must fail before Stripe client creation")

    monkeypatch.setattr(stripe_billing, "_stripe_client", unexpected_client)
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)

    with pytest.raises(HTTPException) as exc_info:
        stripe_billing.parse_webhook(b"123456789", "sig")

    assert exc_info.value.status_code == 413
    assert exc_info.value.detail == "Stripe webhook payload is too large"


def test_oversized_signature_is_rejected_before_stripe_client_or_secret_lookup(monkeypatch):
    monkeypatch.setattr(stripe_billing, "MAX_STRIPE_SIGNATURE_CHARS", 8)

    def unexpected_client():
        raise AssertionError("oversized signature must fail before Stripe client creation")

    monkeypatch.setattr(stripe_billing, "_stripe_client", unexpected_client)
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)

    with pytest.raises(HTTPException) as exc_info:
        stripe_billing.parse_webhook(b"{}", "s" * 9)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Stripe-Signature header is too large"


def test_missing_signature_is_rejected_before_stripe_client_creation(monkeypatch):
    def unexpected_client():
        raise AssertionError("missing signature must fail before Stripe client creation")

    monkeypatch.setattr(stripe_billing, "_stripe_client", unexpected_client)
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)

    with pytest.raises(HTTPException) as exc_info:
        stripe_billing.parse_webhook(b"{}", None)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Stripe-Signature header is required"


def test_missing_webhook_secret_is_rejected_before_stripe_client_creation(monkeypatch):
    def unexpected_client():
        raise AssertionError("missing webhook secret must fail before Stripe client creation")

    monkeypatch.setattr(stripe_billing, "_stripe_client", unexpected_client)
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)

    with pytest.raises(HTTPException) as exc_info:
        stripe_billing.parse_webhook(b"{}", "sig_test")

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "STRIPE_WEBHOOK_SECRET is not configured"


def test_signature_at_limit_still_reaches_signature_verification(monkeypatch):
    monkeypatch.setattr(stripe_billing, "MAX_STRIPE_SIGNATURE_CHARS", 8)
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_private_test_value")
    client = FakeStripeClient()
    monkeypatch.setattr(stripe_billing, "_stripe_client", lambda: client)

    event = stripe_billing.parse_webhook(b"{}", "s" * 8)

    assert event["id"] == "evt_test"
    assert len(client.calls) == 1
    assert client.calls[0][1] == "s" * 8


def test_payload_at_limit_still_reaches_signature_verification(monkeypatch):
    monkeypatch.setattr(stripe_billing, "MAX_WEBHOOK_PAYLOAD_BYTES", 8)
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_private_test_value")
    client = FakeStripeClient()
    monkeypatch.setattr(stripe_billing, "_stripe_client", lambda: client)

    event = stripe_billing.parse_webhook(b"12345678", "sig_test")

    assert event["id"] == "evt_test"
    assert len(client.calls) == 1
    payload, signature, secret = client.calls[0]
    assert payload == b"12345678"
    assert signature == "sig_test"
    assert secret == "whsec_private_test_value"


def test_invalid_signature_does_not_chain_provider_exception(monkeypatch):
    class RejectingClient:
        def construct_event(self, payload: bytes, signature: str, secret: str):
            raise RuntimeError(f"provider rejected {signature} using {secret}")

    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_private_test_value")
    monkeypatch.setattr(stripe_billing, "_stripe_client", lambda: RejectingClient())

    with pytest.raises(HTTPException) as exc_info:
        stripe_billing.parse_webhook(b"{}", "sig_private_test_value")

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid Stripe webhook signature"
    assert exc_info.value.__cause__ is None


def test_payload_limit_is_conservative_for_normal_stripe_events():
    assert stripe_billing.MAX_WEBHOOK_PAYLOAD_BYTES == 1_000_000
    assert stripe_billing.MAX_STRIPE_SIGNATURE_CHARS == 8_192
