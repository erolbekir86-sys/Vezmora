from __future__ import annotations

import os
import sys

# Vercel's source bundle is read-only. Prefer a persistent database when one
# is configured. DATABASE_URL/POSTGRES_URL are bridged into the existing
# remote DB interface so the rest of Vezmora can stay storage-agnostic.
postgres_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
if postgres_url:
    # Reuse the existing remote-store interface without replacing the real
    # Turso package for non-Postgres deployments.
    from app import postgres_compat as _postgres_compat
    sys.modules["turso_serverless"] = _postgres_compat
    os.environ.setdefault("TURSO_DATABASE_URL", postgres_url)

if os.getenv("VERCEL"):
    os.environ.setdefault("VEZMORA_SERVERLESS", "true")
    if not os.getenv("TURSO_DATABASE_URL"):
        os.environ.setdefault("VEZMORA_DB_PATH", "/tmp/.vezmora.db")
        os.environ.setdefault("VEZMORA_DATA_DIR", "/tmp")

# The Postgres schema is provisioned separately in Neon. Avoid running the
# SQLite bootstrap DDL against Postgres and only verify connectivity instead.
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
