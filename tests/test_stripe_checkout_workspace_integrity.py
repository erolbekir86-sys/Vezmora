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
    monkeypatch.setattr(stripe_billing, "workspace_id_by_stripe_customer", lambda customer_id: None)

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


def test_checkout_completed_rejects_customer_already_linked_to_other_workspace(monkeypatch):
    touched = {"recorded": False, "billing": False}

    monkeypatch.setattr(stripe_billing, "workspace_id_by_stripe_customer", lambda customer_id: 9)
    monkeypatch.setattr(
        stripe_billing,
        "record_billing_event",
        lambda *args, **kwargs: touched.__setitem__("recorded", True) or True,
    )
    monkeypatch.setattr(
        stripe_billing,
        "set_workspace_billing",
        lambda *args, **kwargs: touched.__setitem__("billing", True),
    )

    event = {
        "id": "evt_customer_workspace_mismatch",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "client_reference_id": "7",
                "customer": "cus_existing",
                "subscription": "sub_test",
                "metadata": {"workspace_id": "7", "plan": "start", "trial_days": "0"},
            }
        },
    }

    with pytest.raises(HTTPException) as excinfo:
        stripe_billing.apply_webhook(event)

    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Stripe customer is linked to a different workspace"
    assert touched == {"recorded": False, "billing": False}


def test_subscription_event_accepts_customer_and_metadata_for_same_workspace(monkeypatch):
    recorded = []
    billing_calls = []

    monkeypatch.setattr(stripe_billing, "workspace_id_by_stripe_customer", lambda customer_id: 7)
    monkeypatch.setattr(stripe_billing, "get_workspace_settings", lambda workspace_id: {"plan": "start"})
    monkeypatch.setattr(
        stripe_billing,
        "record_billing_event",
        lambda workspace_id, event_id, event_type, event: recorded.append((workspace_id, event_id, event_type)) or True,
    )
    monkeypatch.setattr(stripe_billing, "set_workspace_billing", lambda *args, **kwargs: billing_calls.append((args, kwargs)))

    event = {
        "id": "evt_customer_workspace_match",
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_test",
                "customer": "cus_existing",
                "status": "active",
                "metadata": {"workspace_id": "7", "plan": "growth"},
            }
        },
    }

    result = stripe_billing.apply_webhook(event)

    assert result == {"ok": True, "workspace_id": 7, "type": "customer.subscription.updated"}
    assert recorded == [(7, "evt_customer_workspace_match", "customer.subscription.updated")]
    assert billing_calls[0][0] == (7,)
    assert billing_calls[0][1]["customer_id"] == "cus_existing"
