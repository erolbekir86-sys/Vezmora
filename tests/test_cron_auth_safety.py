from __future__ import annotations

import pytest
from fastapi import HTTPException

import app.main as main_module
from app import cron_auth_safety


def test_cron_auth_fails_closed_when_secret_missing(monkeypatch) -> None:
    monkeypatch.delenv("CRON_SECRET", raising=False)

    with pytest.raises(HTTPException) as exc:
        cron_auth_safety.require_cron_constant_time("Bearer anything")

    assert exc.value.status_code == 503


def test_cron_auth_rejects_wrong_or_missing_bearer(monkeypatch) -> None:
    monkeypatch.setenv("CRON_SECRET", "private-cron-secret")

    for provided in (None, "", "Bearer wrong-secret", "Basic private-cron-secret"):
        with pytest.raises(HTTPException) as exc:
            cron_auth_safety.require_cron_constant_time(provided)
        assert exc.value.status_code == 401


def test_cron_auth_accepts_exact_bearer_using_compare_digest(monkeypatch) -> None:
    monkeypatch.setenv("CRON_SECRET", "private-cron-secret")
    calls: list[tuple[bytes, bytes]] = []
    original = cron_auth_safety.hmac.compare_digest

    def recording_compare_digest(left: bytes, right: bytes) -> bool:
        calls.append((left, right))
        return original(left, right)

    monkeypatch.setattr(cron_auth_safety.hmac, "compare_digest", recording_compare_digest)

    cron_auth_safety.require_cron_constant_time("Bearer private-cron-secret")

    assert calls == [(b"Bearer private-cron-secret", b"Bearer private-cron-secret")]


def test_main_cron_routes_use_hardened_validator() -> None:
    assert main_module._require_cron is cron_auth_safety.require_cron_constant_time
