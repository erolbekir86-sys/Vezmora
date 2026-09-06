from __future__ import annotations

from app.runtime_diagnostics import runtime_health_payload, storage_backend


def test_storage_backend_reports_sqlite_without_remote_url(monkeypatch):
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    assert storage_backend() == "sqlite"


def test_storage_backend_reports_real_turso(monkeypatch):
    monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://example.turso.io")
    assert storage_backend() == "turso"
    assert runtime_health_payload()["data_path"] == "remote"


def test_storage_backend_reports_postgres_compat_url(monkeypatch):
    monkeypatch.setenv("TURSO_DATABASE_URL", "postgresql://user:secret@example.invalid/db")
    payload = runtime_health_payload()
    assert storage_backend() == "postgres"
    assert payload["storage_backend"] == "postgres"
    assert payload["data_path"] == "remote"
    assert "example.invalid" not in repr(payload)
    assert "secret" not in repr(payload)


def test_storage_backend_accepts_legacy_postgres_scheme(monkeypatch):
    monkeypatch.setenv("TURSO_DATABASE_URL", "postgres://user:secret@example.invalid/db")
    assert storage_backend() == "postgres"
