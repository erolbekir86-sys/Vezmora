from __future__ import annotations

import app.autopilot as autopilot
import app.main as main_module
import app.store as store
from app import execution_log_safety


def test_execution_audit_redacts_nested_credentials_before_persistence(monkeypatch) -> None:
    monkeypatch.setenv("META_APP_SECRET", "meta-runtime-secret")
    captured: dict[str, object] = {}

    def fake_original(workspace_id, approval_id, user_id, provider, action_type, request, result, status):
        captured.update(
            workspace_id=workspace_id,
            approval_id=approval_id,
            user_id=user_id,
            provider=provider,
            action_type=action_type,
            request=request,
            result=result,
            status=status,
        )
        return 91

    monkeypatch.setattr(execution_log_safety, "_ORIGINAL_LOG_EXECUTION", fake_original)

    log_id = execution_log_safety.log_execution_safely(
        4,
        8,
        12,
        "meta",
        "meta.pause_campaign",
        {
            "campaign_id": "123456",
            "budget": 500,
            "note": "access_token=request-token-abc",
        },
        {
            "status": "failed",
            "error": "provider meta-runtime-secret",
            "nested": ["Bearer nested-token-xyz", {"password": "password=inline-pass"}],
        },
        "failed",
    )

    assert log_id == 91
    rendered = repr({"request": captured["request"], "result": captured["result"]})
    for secret in ("request-token-abc", "meta-runtime-secret", "nested-token-xyz", "inline-pass"):
        assert secret not in rendered
    assert captured["request"]["campaign_id"] == "123456"
    assert captured["request"]["budget"] == 500
    assert captured["result"]["status"] == "failed"
    assert rendered.count("[REDACTED]") >= 4


def test_execution_audit_preserves_non_secret_values() -> None:
    value = {
        "campaign_id": "987654",
        "changes": {"status": "PAUSED", "daily_budget": 299.5},
        "items": [1, True, None],
    }
    assert execution_log_safety._redact_value(value) == value


def test_execution_callers_bind_safe_audit_logger() -> None:
    assert getattr(store, "_vexmera_execution_log_safety_installed", False) is True
    assert store.log_execution is execution_log_safety.log_execution_safely
    assert main_module.log_execution is execution_log_safety.log_execution_safely
    assert autopilot.log_execution is execution_log_safety.log_execution_safely
