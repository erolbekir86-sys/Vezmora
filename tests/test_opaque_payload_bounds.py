from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models import ApprovalCreate, CoreActionCreate, JobCreateRequest


def _large_payload() -> dict[str, str]:
    return {"blob": "x" * (64 * 1024)}


def test_normal_opaque_payloads_remain_allowed() -> None:
    payload = {"campaign_id": "123", "budget": 2500, "nested": {"enabled": False}}

    approval = ApprovalCreate(
        action_type="google.set_daily_budget",
        title="Preview budget change",
        description="Recommendation only",
        payload=payload,
    )
    job = JobCreateRequest(kind="sync_google", payload=payload)
    action = CoreActionCreate(
        title="Review campaign",
        rationale="Performance changed",
        action_type="review",
        payload=payload,
    )

    assert approval.payload == payload
    assert job.payload == payload
    assert action.payload == payload


@pytest.mark.parametrize(
    "factory",
    [
        lambda payload: ApprovalCreate(
            action_type="google.set_daily_budget",
            title="Preview budget change",
            description="Recommendation only",
            payload=payload,
        ),
        lambda payload: JobCreateRequest(kind="sync_google", payload=payload),
        lambda payload: CoreActionCreate(
            title="Review campaign",
            rationale="Performance changed",
            action_type="review",
            payload=payload,
        ),
    ],
)
def test_oversized_opaque_payloads_fail_validation(factory) -> None:
    with pytest.raises(ValidationError, match="payload is too large"):
        factory(_large_payload())


def test_multibyte_payload_limit_is_measured_in_encoded_bytes() -> None:
    with pytest.raises(ValidationError, match="payload is too large"):
        JobCreateRequest(kind="sync_meta", payload={"blob": "å" * 40_000})
