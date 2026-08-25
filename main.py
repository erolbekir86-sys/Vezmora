from __future__ import annotations

import os
import sys

# Vercel's deployed source bundle is read-only. Prefer persistent Postgres
# whenever DATABASE_URL/POSTGRES_URL is configured. Some early beta Vercel
# setups created empty legacy variables, so do not let empty values block the
# production bootstrap.
postgres_url = (os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or "").strip()
if postgres_url:
    # Reuse the existing remote-store interface while translating Vezmora's
    # SQLite-style DB-API calls to PostgreSQL through postgres_compat.
    from app import postgres_compat as _postgres_compat

    sys.modules["turso_serverless"] = _postgres_compat
    # Override an empty/legacy TURSO_DATABASE_URL so store.py definitely uses
    # the Postgres compatibility connection when DATABASE_URL is present.
    os.environ["TURSO_DATABASE_URL"] = postgres_url

if os.getenv("VERCEL"):
    # Vercel is always serverless for this deployment. Override any empty or
    # stale beta value rather than relying on setdefault().
    os.environ["VEZMORA_SERVERLESS"] = "true"

    # Only use /tmp as a smoke-test fallback when no persistent remote database
    # is configured at all.
    if not postgres_url and not (os.getenv("TURSO_DATABASE_URL") or "").strip():
        os.environ["VEZMORA_DB_PATH"] = "/tmp/.vezmora.db"
        os.environ["VEZMORA_DATA_DIR"] = "/tmp"

# An empty OPENAI_MODEL environment variable should not erase the safe default.
if not (os.getenv("OPENAI_MODEL") or "").strip():
    os.environ["OPENAI_MODEL"] = "gpt-5.6-terra"

# The Postgres schema is provisioned separately in Neon. Avoid running the
# SQLite bootstrap DDL against Postgres and verify connectivity instead.
if postgres_url:
    import app.store as _store

    def _verify_database() -> None:
        with _store._connect() as con:
            con.execute("SELECT 1")

    _store.init_db = _verify_database

from app.main import app, main

__all__ = ["app", "main"]

if __name__ == "__main__":
    main()
