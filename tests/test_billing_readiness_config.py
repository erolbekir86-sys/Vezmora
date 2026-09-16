from app import billing


def _stub_billing_dependencies(monkeypatch) -> None:
    monkeypatch.setattr(
        billing,
        "get_workspace_settings",
        lambda workspace_id: {
            "plan": "start",
            "billing_status": "trialing",
            "trial_ends_at": None,
            "stripe_customer_id": None,
            "stripe_subscription_id": None,
        },
    )
    monkeypatch.setattr(billing, "usage_summary", lambda workspace_id: {})
    monkeypatch.setattr(billing, "current_stripe_catalog_reconciled", lambda: True)


def test_checkout_readiness_rejects_whitespace_only_stripe_secret_key(monkeypatch):
    _stub_billing_dependencies(monkeypatch)
    monkeypatch.setenv("STRIPE_SECRET_KEY", "   \t")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")

    status = billing.billing_status(1)

    assert status["checkout_ready"] is False


def test_checkout_readiness_rejects_whitespace_only_webhook_secret(monkeypatch):
    _stub_billing_dependencies(monkeypatch)
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_example")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "  \n ")

    status = billing.billing_status(1)

    assert status["checkout_ready"] is False


def test_checkout_readiness_rejects_unreconciled_catalog(monkeypatch):
    _stub_billing_dependencies(monkeypatch)
    monkeypatch.setattr(billing, "current_stripe_catalog_reconciled", lambda: False)
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_example")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")

    status = billing.billing_status(1)

    assert status["checkout_ready"] is False


def test_checkout_readiness_accepts_verified_stripe_catalog(monkeypatch):
    _stub_billing_dependencies(monkeypatch)
    monkeypatch.setenv("STRIPE_SECRET_KEY", " sk_test_example ")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", " whsec_test ")

    status = billing.billing_status(1)

    assert status["checkout_ready"] is True
