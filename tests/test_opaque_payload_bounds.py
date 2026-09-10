from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models import (
    ApprovalCreate,
    BillingCheckoutRequest,
    CoreActionCreate,
    JobCreateRequest,
    MAX_OPAQUE_PAYLOAD_BYTES,
)


def _approval(payload):
    return ApprovalCreate(
        action_type="review",
        title="Review campaign",
        description="Recommendation only",
        payload=payload,
    )


def _core_action(payload):
    return CoreActionCreate(
        title="Review campaign",
        rationale="Performance changed",
        action_type="review",
        payload=payload,
    )


def test_current_checkout_and_core_models_remain_available() -> None:
    assert BillingCheckoutRequest(plan="start").plan == "start"
    assert _core_action({"campaign_id": "123"}).payload == {"campaign_id": "123"}


@pytest.mark.parametrize(
    "factory",
    [
        _approval,
        lambda payload: JobCreateRequest(kind="sync_google", payload=payload),
        _core_action,
    ],
)
def test_normal_opaque_payloads_remain_allowed(factory) -> None:
    payload = {"campaign_id": "123", "budget": 2500, "nested": {"enabled": False}}
    assert factory(payload).payload == payload


@pytest.mark.parametrize(
    "factory",
    [
        _approval,
        lambda payload: JobCreateRequest(kind="sync_google", payload=payload),
        _core_action,
    ],
)
def test_oversized_opaque_payloads_fail_validation(factory) -> None:
    with pytest.raises(ValidationError, match="payload is too large"):
        factory({"blob": "x" * MAX_OPAQUE_PAYLOAD_BYTES})


def test_multibyte_payload_limit_is_measured_in_encoded_bytes() -> None:
    with pytest.raises(ValidationError, match="payload is too large"):
        JobCreateRequest(kind="sync_meta", payload={"blob": "å" * 40_000})


def test_non_json_safe_payload_fails_validation() -> None:
    with pytest.raises(ValidationError, match="payload must be JSON serializable"):
        _approval({"bad": object()})
