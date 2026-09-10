from __future__ import annotations

import pytest
from fastapi import HTTPException

from app import stripe_billing, stripe_event_safety
import app.main as main_module


def _event(event_id: object = "evt_test", event_type: object = "invoice.payment_failed") -> dict[str, object]:
    return {"id": event_id, "type": event_type, "data": {"object": {}}}


def _parse(monkeypatch, event: dict[str, object]):
    monkeypatch.setattr(
        stripe_event_safety._bounded_parse_webhook,
        "_original",
        lambda payload, signature: event,
    )
    return stripe_event_safety._bounded_parse_webhook(b"{}", "sig_test")


def test_installed_wrapper_is_bound_before_main_routes() -> None:
    assert stripe_billing.parse_webhook is stripe_event_safety._bounded_parse_webhook
    assert main_module.parse_webhook is stripe_event_safety._bounded_parse_webhook


def test_accepts_normal_verified_event(monkeypatch) -> None:
    expected = _event()
    assert _parse(monkeypatch, expected) is expected


def test_accepts_identifier_boundary(monkeypatch) -> None:
    expected = _event("e" * 255, "t" * 255)
    assert _parse(monkeypatch, expected) is expected


@pytest.mark.parametrize("event_id", [None, "", 123, "e" * 256])
def test_rejects_invalid_verified_event_id(monkeypatch, event_id: object) -> None:
    with pytest.raises(HTTPException) as exc_info:
        _parse(monkeypatch, _event(event_id=event_id))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid Stripe webhook event id"


@pytest.mark.parametrize("event_type", [None, "", 123, "t" * 256])
def test_rejects_invalid_verified_event_type(monkeypatch, event_type: object) -> None:
    with pytest.raises(HTTPException) as exc_info:
        _parse(monkeypatch, _event(event_type=event_type))

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid Stripe webhook event type"
