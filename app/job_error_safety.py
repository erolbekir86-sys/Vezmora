from __future__ import annotations

from functools import wraps

from . import store as _store
from .secret_redaction import redact_sensitive_text

_ORIGINAL_FAIL_JOB = _store.fail_job


@wraps(_ORIGINAL_FAIL_JOB)
def fail_job_safely(job_id: int, error: str, retry: bool = False) -> None:
    """Redact credentials before a worker exception is persisted in jobs.error_text."""
    safe_error = redact_sensitive_text(error)
    _ORIGINAL_FAIL_JOB(job_id, safe_error, retry=retry)


def install_job_error_safety() -> None:
    """Install sanitized job failures before jobs.py binds store.fail_job."""
    if getattr(_store, "_vexmera_job_error_safety_installed", False):
        return
    _store.fail_job = fail_job_safely
    _store._vexmera_job_error_safety_installed = True
