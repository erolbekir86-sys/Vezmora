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


def test_apply_webhook_rejects_missing_event_type_before_side_effects(monkeypatch):
    touched = {"recorded": False, "billing": False}

    def fake_record(*args, **kwargs):
        touched["recorded"] = True
        return True

    def fake_set_billing(*args, **kwargs):
        touched["billing"] = True

    monkeypatch.setattr(stripe_billing, "record_billing_event", fake_record)
    monkeypatch.setattr(stripe_billing, "set_workspace_billing", fake_set_billing)

    event = {
        "id": "evt_missing_type",
        "data": {"object": {"metadata": {"workspace_id": "7"}}},
    }

    with pytest.raises(HTTPException) as excinfo:
        stripe_billing.apply_webhook(event)

    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Stripe webhook event type is required"
    assert touched == {"recorded": False, "billing": False}


def test_apply_webhook_keeps_duplicate_event_idempotency(monkeypatch):
    touched = {"recorded": False, "billing": False}

    monkeypatch.setattr(stripe_billing, "_billing_event_processed", lambda event_id: event_id == "evt_test_duplicate")
    monkeypatch.setattr(
        stripe_billing,
        "record_billing_event",
        lambda *args, **kwargs: touched.__setitem__("recorded", True),
    )
    monkeypatch.setattr(
        stripe_billing,
        "set_workspace_billing",
        lambda *args, **kwargs: touched.__setitem__("billing", True),
    )

    event = {
        "id": "evt_test_duplicate",
        "type": "invoice.payment_failed",
        "data": {"object": {"metadata": {"workspace_id": "7"}}},
    }

    result = stripe_billing.apply_webhook(event)

    assert result == {"ok": True, "duplicate": True}
    assert touched == {"recorded": False, "billing": False}


@pytest.mark.parametrize(
    "data",
    [
        [],
        "not-an-object",
        {"object": []},
        {"object": {"metadata": "not-an-object"}},
    ],
)
def test_apply_webhook_rejects_malformed_signed_event_shapes_before_side_effects(monkeypatch, data):
    touched = {"recorded": False, "billing": False}

    def fake_record(*args, **kwargs):
        touched["recorded"] = True
        return True

    def fake_set_billing(*args, **kwargs):
        touched["billing"] = True

    monkeypatch.setattr(stripe_billing, "record_billing_event", fake_record)
    monkeypatch.setattr(stripe_billing, "set_workspace_billing", fake_set_billing)

    event = {"id": "evt_malformed", "type": "invoice.payment_failed", "data": data}

    with pytest.raises(HTTPException) as excinfo:
        stripe_billing.apply_webhook(event)

    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Invalid Stripe webhook payload"
    assert touched == {"recorded": False, "billing": False}


def test_checkout_completed_treats_invalid_trial_days_as_non_trialing(monkeypatch):
    billing_calls = []

    monkeypatch.setattr(stripe_billing, "_billing_event_processed", lambda event_id: False)
    monkeypatch.setattr(stripe_billing, "record_billing_event", lambda *args, **kwargs: True)
    monkeypatch.setattr(stripe_billing, "set_workspace_billing", lambda *args, **kwargs: billing_calls.append(kwargs))

    event = {
        "id": "evt_bad_trial_days",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": "cus_test",
                "subscription": "sub_test",
                "metadata": {"workspace_id": "7", "plan": "start", "trial_days": "unexpected"},
            }
        },
    }

    result = stripe_billing.apply_webhook(event)

    assert result["ok"] is True
    assert billing_calls[0]["billing_status"] == "active"
