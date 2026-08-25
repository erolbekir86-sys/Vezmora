from __future__ import annotations

import os

# Vercel's deployed source bundle is read-only. Until a persistent Turso
# database is configured, use /tmp so the app can boot for smoke testing.
# /tmp is ephemeral and must not be treated as production persistence.
if os.getenv("VERCEL"):
    os.environ.setdefault("VEZMORA_SERVERLESS", "true")
    if not os.getenv("TURSO_DATABASE_URL"):
        os.environ.setdefault("VEZMORA_DB_PATH", "/tmp/.vezmora.db")
        os.environ.setdefault("VEZMORA_DATA_DIR", "/tmp")

from app.main import app, main

__all__ = ["app", "main"]

if __name__ == "__main__":
    main()
