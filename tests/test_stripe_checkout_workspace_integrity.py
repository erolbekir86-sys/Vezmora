from fastapi import HTTPException
import pytest

from app import stripe_billing


def test_checkout_completed_rejects_mismatched_workspace_references_before_side_effects(monkeypatch):
    touched = {"recorded": False, "billing": False}

    def fake_record(*args, **kwargs):
        touched["recorded"] = True
        return True

    def fake_set_billing(*args, **kwargs):
        touched["billing"] = True

    monkeypatch.setattr(stripe_billing, "record_billing_event", fake_record)
    monkeypatch.setattr(stripe_billing, "set_workspace_billing", fake_set_billing)

    event = {
        "id": "evt_workspace_mismatch",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "client_reference_id": "8",
                "customer": "cus_test",
                "subscription": "sub_test",
                "metadata": {"workspace_id": "7", "plan": "start", "trial_days": "0"},
            }
        },
    }

    with pytest.raises(HTTPException) as excinfo:
        stripe_billing.apply_webhook(event)

    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Stripe checkout workspace reference mismatch"
    assert touched == {"recorded": False, "billing": False}


def test_checkout_completed_accepts_matching_workspace_references(monkeypatch):
    recorded = []
    billing_calls = []

    monkeypatch.setattr(
        stripe_billing,
        "record_billing_event",
        lambda workspace_id, event_id, event_type, event: recorded.append((workspace_id, event_id, event_type)) or True,
    )
    monkeypatch.setattr(stripe_billing, "set_workspace_billing", lambda *args, **kwargs: billing_calls.append((args, kwargs)))

    event = {
        "id": "evt_workspace_match",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "client_reference_id": "7",
                "customer": "cus_test",
                "subscription": "sub_test",
                "metadata": {"workspace_id": "7", "plan": "start", "trial_days": "0"},
            }
        },
    }

    result = stripe_billing.apply_webhook(event)

    assert result == {"ok": True, "workspace_id": 7, "type": "checkout.session.completed"}
    assert recorded == [(7, "evt_workspace_match", "checkout.session.completed")]
    assert billing_calls[0][0] == (7,)
    assert billing_calls[0][1]["billing_status"] == "active"
