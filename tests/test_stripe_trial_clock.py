from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app import stripe_billing


def test_checkout_trial_uses_only_remaining_workspace_trial(monkeypatch):
    monkeypatch.setenv("VEZMORA_TRIAL_DAYS", "14")
    trial_end = (datetime.now(timezone.utc) + timedelta(days=2, hours=1)).isoformat()

    days = stripe_billing._trial_days(
        {
            "trial_ends_at": trial_end,
            "stripe_customer_id": None,
            "stripe_subscription_id": None,
        }
    )

    assert days == 3


def test_checkout_trial_is_not_restarted_after_workspace_trial_expires(monkeypatch):
    monkeypatch.setenv("VEZMORA_TRIAL_DAYS", "14")
    trial_end = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()

    days = stripe_billing._trial_days(
        {
            "trial_ends_at": trial_end,
            "stripe_customer_id": None,
            "stripe_subscription_id": None,
        }
    )

    assert days == 0


def test_existing_stripe_customer_never_receives_a_new_beta_trial(monkeypatch):
    monkeypatch.setenv("VEZMORA_TRIAL_DAYS", "14")
    trial_end = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()

    days = stripe_billing._trial_days(
        {
            "trial_ends_at": trial_end,
            "stripe_customer_id": "cus_existing",
            "stripe_subscription_id": None,
        }
    )

    assert days == 0
