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


def test_payload_limit_is_conservative_for_normal_stripe_events():
    assert stripe_billing.MAX_WEBHOOK_PAYLOAD_BYTES == 1_000_000
