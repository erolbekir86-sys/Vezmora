from __future__ import annotations

import pytest

from app import stripe_billing


def _checkout_event() -> dict:
    return {
        "id": "evt_retry_safe",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": "cus_retry",
                "subscription": "sub_retry",
                "client_reference_id": "7",
                "metadata": {"workspace_id": "7", "plan": "start", "trial_days": "0"},
            }
        },
    }


def test_failed_billing_projection_does_not_claim_event(monkeypatch) -> None:
    recorded = []

    def fail_billing(*args, **kwargs):
        raise RuntimeError("temporary database failure")

    def record(*args, **kwargs):
        recorded.append(args)
        return True

    monkeypatch.setattr(stripe_billing, "set_workspace_billing", fail_billing)
    monkeypatch.setattr(stripe_billing, "record_billing_event", record)

    with pytest.raises(RuntimeError, match="temporary database failure"):
        stripe_billing.apply_webhook(_checkout_event())

    assert recorded == []


def test_successful_billing_projection_is_recorded_after_write(monkeypatch) -> None:
    calls = []

    def set_billing(*args, **kwargs):
        calls.append("billing")

    def record(*args, **kwargs):
        calls.append("record")
        return True

    monkeypatch.setattr(stripe_billing, "set_workspace_billing", set_billing)
    monkeypatch.setattr(stripe_billing, "record_billing_event", record)

    result = stripe_billing.apply_webhook(_checkout_event())

    assert calls == ["billing", "record"]
    assert result == {"ok": True, "workspace_id": 7, "type": "checkout.session.completed"}
