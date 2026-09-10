from __future__ import annotations

import app.jobs as jobs
import app.store as store
from app import google_ads_diagnostics, job_error_safety, secret_redaction


def test_persisted_job_error_redacts_runtime_and_inline_credentials(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-private-worker-key")
    monkeypatch.setenv("DATABASE_URL", "postgresql://worker:dbpass@db.example/vexmera")
    captured: dict[str, object] = {}

    def fake_original(job_id: int, error: str, retry: bool = False) -> None:
        captured.update(job_id=job_id, error=error, retry=retry)

    monkeypatch.setattr(job_error_safety, "_ORIGINAL_FAIL_JOB", fake_original)

    job_error_safety.fail_job_safely(
        23,
        "Provider failed sk-private-worker-key at postgresql://worker:dbpass@db.example/vexmera password=inline-pass request_id=req_123",
        retry=True,
    )

    rendered = str(captured["error"])
    assert captured["job_id"] == 23
    assert captured["retry"] is True
    assert "sk-private-worker-key" not in rendered
    assert "postgresql://worker:dbpass@db.example/vexmera" not in rendered
    assert "inline-pass" not in rendered
    assert "request_id=req_123" in rendered
    assert rendered.count("[REDACTED]") >= 3


def test_non_secret_worker_error_context_is_preserved(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_original(job_id: int, error: str, retry: bool = False) -> None:
        captured.update(job_id=job_id, error=error, retry=retry)

    monkeypatch.setattr(job_error_safety, "_ORIGINAL_FAIL_JOB", fake_original)
    message = "HTTPException: Google Ads customer ID is required"

    job_error_safety.fail_job_safely(24, message, retry=False)

    assert captured == {"job_id": 24, "error": message, "retry": False}


def test_all_error_surfaces_share_one_secret_redactor() -> None:
    assert google_ads_diagnostics._redact_sensitive_text is secret_redaction.redact_sensitive_text


def test_worker_binds_sanitized_fail_job_before_execution() -> None:
    assert getattr(store, "_vexmera_job_error_safety_installed", False) is True
    assert store.fail_job is job_error_safety.fail_job_safely
    assert jobs.fail_job is job_error_safety.fail_job_safely
