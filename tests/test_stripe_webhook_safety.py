from fastapi import HTTPException
import pytest

from app import stripe_billing


def test_apply_webhook_rejects_missing_event_id_before_side_effects(monkeypatch):
    touched = {"recorded": False, "billing": False}

    def fake_record(*args, **kwargs):
        touched["recorded"] = True
        return True

    def fake_set_billing(*args, **kwargs):
        touched["billing"] = True

    monkeypatch.setattr(stripe_billing, "record_billing_event", fake_record)
    monkeypatch.setattr(stripe_billing, "set_workspace_billing", fake_set_billing)

    event = {
        "type": "invoice.payment_failed",
        "data": {"object": {"metadata": {"workspace_id": "7"}}},
    }

    with pytest.raises(HTTPException) as excinfo:
        stripe_billing.apply_webhook(event)

    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Stripe webhook event id is required"
    assert touched == {"recorded": False, "billing": False}


def test_apply_webhook_keeps_duplicate_event_idempotency(monkeypatch):
    recorded = []

    def fake_record(workspace_id, event_id, event_type, event):
        recorded.append((workspace_id, event_id, event_type))
        return False

    monkeypatch.setattr(stripe_billing, "record_billing_event", fake_record)

    event = {
        "id": "evt_test_duplicate",
        "type": "invoice.payment_failed",
        "data": {"object": {"metadata": {"workspace_id": "7"}}},
    }

    result = stripe_billing.apply_webhook(event)

    assert result == {"ok": True, "duplicate": True}
    assert recorded == [(7, "evt_test_duplicate", "invoice.payment_failed")]
