from __future__ import annotations

from app import billing_event_minimization as minimization
from app import store
from app import stripe_billing


def _stripe_event() -> dict:
    return {
        "id": "evt_123",
        "type": "checkout.session.completed",
        "created": 1789042000,
        "livemode": False,
        "account": "acct_should_not_persist",
        "request": {"id": "req_private", "idempotency_key": "secret-ish"},
        "data": {
            "object": {
                "id": "cs_test_123",
                "object": "checkout.session",
                "status": "complete",
                "customer": "cus_123",
                "customer_email": "buyer@example.com",
                "customer_details": {
                    "email": "buyer@example.com",
                    "name": "Private Buyer",
                    "phone": "+46700000000",
                    "address": {"line1": "Private street 1"},
                },
                "payment_method_types": ["card"],
                "subscription": "sub_123",
                "metadata": {
                    "workspace_id": "42",
                    "plan": "growth",
                    "trial_days": "14",
                    "campaign_name": "private campaign",
                    "customer_note": "do not persist",
                },
            },
            "previous_attributes": {"customer_email": "old@example.com"},
        },
    }


def test_minimal_payload_keeps_only_small_non_customer_audit_fields() -> None:
    minimized = minimization.minimal_billing_event_payload(_stripe_event())

    assert minimized == {
        "id": "evt_123",
        "type": "checkout.session.completed",
        "created": 1789042000,
        "livemode": False,
        "data": {
            "object": {
                "id": "cs_test_123",
                "object": "checkout.session",
                "status": "complete",
                "metadata": {
                    "workspace_id": "42",
                    "plan": "growth",
                    "trial_days": "14",
                },
            }
        },
    }


def test_minimal_payload_drops_customer_and_payment_details_recursively() -> None:
    serialized = repr(minimization.minimal_billing_event_payload(_stripe_event()))

    for forbidden in (
        "buyer@example.com",
        "Private Buyer",
        "+46700000000",
        "Private street 1",
        "cus_123",
        "sub_123",
        "card",
        "acct_should_not_persist",
        "req_private",
        "private campaign",
        "do not persist",
        "old@example.com",
    ):
        assert forbidden not in serialized


def test_minimal_payload_handles_malformed_optional_shapes_without_raising() -> None:
    payload = {
        "id": "evt_badshape",
        "type": "invoice.payment_failed",
        "created": "not-a-number",
        "livemode": "false",
        "data": ["not-a-dict"],
    }

    assert minimization.minimal_billing_event_payload(payload) == {
        "id": "evt_badshape",
        "type": "invoice.payment_failed",
    }


def test_record_wrapper_passes_minimized_copy_and_preserves_idempotence_result(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_original(workspace_id, provider_event_id, event_type, payload):
        captured.update(
            workspace_id=workspace_id,
            provider_event_id=provider_event_id,
            event_type=event_type,
            payload=payload,
        )
        return False

    monkeypatch.setattr(minimization, "_ORIGINAL_RECORD_BILLING_EVENT", fake_original)

    result = minimization.record_billing_event_minimized(
        42,
        "evt_123",
        "checkout.session.completed",
        _stripe_event(),
    )

    assert result is False
    assert captured["workspace_id"] == 42
    assert captured["provider_event_id"] == "evt_123"
    assert captured["event_type"] == "checkout.session.completed"
    assert captured["payload"] == minimization.minimal_billing_event_payload(_stripe_event())


def test_minimization_is_installed_before_stripe_billing_binds_store_helper() -> None:
    assert getattr(store, "_vexmera_billing_event_minimization_installed", False) is True
    assert store.record_billing_event is minimization.record_billing_event_minimized
    assert stripe_billing.record_billing_event is minimization.record_billing_event_minimized
