import pytest
from fastapi import HTTPException

from app import stripe_billing, stripe_event_safety


def _event(event_id="evt_test", event_type="invoice.payment_failed"):
    return {"id": event_id, "type": event_type, "data": {"object": {}}}


def test_installed_wrapper_is_bound_before_main_routes():
    assert stripe_billing.parse_webhook is stripe_event_safety._bounded_parse_webhook


def test_rejects_oversized_verified_event_id(monkeypatch):
    monkeypatch.setattr(stripe_event_safety._bounded_parse_webhook, "_original", lambda payload, signature: _event("e" * 256))
    with pytest.raises(HTTPException) as exc:
        stripe_event_safety._bounded_parse_webhook(b"{}", "sig")
    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid Stripe webhook event id"


def test_rejects_oversized_verified_event_type(monkeypatch):
    monkeypatch.setattr(stripe_event_safety._bounded_parse_webhook, "_original", lambda payload, signature: _event(event_type="t" * 256))
    with pytest.raises(HTTPException) as exc:
        stripe_event_safety._bounded_parse_webhook(b"{}", "sig")
    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid Stripe webhook event type"


def test_accepts_normal_verified_event(monkeypatch):
    expected = _event()
    monkeypatch.setattr(stripe_event_safety._bounded_parse_webhook, "_original", lambda payload, signature: expected)
    assert stripe_event_safety._bounded_parse_webhook(b"{}", "sig") is expected
