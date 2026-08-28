from __future__ import annotations

import os
import sys

import httpx

# Vercel's deployed source bundle is read-only. Prefer persistent Postgres
# whenever DATABASE_URL/POSTGRES_URL is configured. Some early beta Vercel
# setups created empty legacy variables, so do not let empty values block the
# production bootstrap.
postgres_url = (os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or "").strip()
if postgres_url:
    # Reuse the existing remote-store interface while translating Vexmera's
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


def _configured(name: str) -> bool:
    return bool((os.getenv(name) or "").strip())


def _database_connection_ok() -> bool:
    if not postgres_url:
        return False
    try:
        import app.store as _store

        with _store._connect() as con:
            row = con.execute("SELECT 1").fetchone()
        return bool(row and int(row[0]) == 1)
    except Exception:
        return False


def _openai_connection_ok() -> bool:
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        return False
    try:
        response = httpx.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=8.0,
        )
        return response.status_code == 200
    except Exception:
        return False


def _https_runtime() -> bool:
    return bool(os.getenv("VERCEL")) or (os.getenv("VEZMORA_APP_URL") or "").lower().startswith("https://")


def _internal_secrets_configured() -> bool:
    return all(_configured(name) for name in ("VEZMORA_APP_URL", "VEZMORA_SECRET_KEY", "CRON_SECRET"))


def _stripe_configured() -> bool:
    return all(
        _configured(name)
        for name in (
            "STRIPE_SECRET_KEY",
            "STRIPE_WEBHOOK_SECRET",
            "STRIPE_PRICE_STARTER",
            "STRIPE_PRICE_GROWTH",
            "STRIPE_PRICE_SCALE",
        )
    )


def _smtp_configured() -> bool:
    return _configured("SMTP_HOST") and _configured("SMTP_FROM")


def _google_oauth_configured() -> bool:
    return all(_configured(name) for name in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI"))


def _meta_oauth_configured() -> bool:
    return all(_configured(name) for name in ("META_APP_ID", "META_APP_SECRET", "META_REDIRECT_URI"))


@app.middleware("http")
async def production_security_headers(request, call_next):
    """Apply low-risk browser security defaults to every Vexmera response."""
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if request.url.path.startswith("/api/") or request.url.path.startswith("/health"):
        response.headers.setdefault("Cache-Control", "no-store")
    if _https_runtime():
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


@app.get("/health/runtime")
def runtime_diagnostics() -> dict[str, object]:
    """Expose only non-secret deployment diagnostics for production debugging."""
    return {
        "ok": True,
        "brand": "Vexmera",
        "vercel": bool(os.getenv("VERCEL")),
        "vercel_env": os.getenv("VERCEL_ENV") or None,
        "git_commit_sha": os.getenv("VERCEL_GIT_COMMIT_SHA") or None,
        "database_url_configured": _configured("DATABASE_URL"),
        "postgres_url_configured": _configured("POSTGRES_URL"),
        "remote_store_configured": _configured("TURSO_DATABASE_URL"),
        "database_connection_ok": _database_connection_ok(),
        "openai_api_key_configured": _configured("OPENAI_API_KEY"),
        "openai_connection_ok": _openai_connection_ok(),
        "openai_model_configured": _configured("OPENAI_MODEL"),
        "serverless_configured": (os.getenv("VEZMORA_SERVERLESS") or "").lower() in {"1", "true", "yes", "on"},
        "app_url_configured": _configured("VEZMORA_APP_URL"),
        "app_secret_configured": _configured("VEZMORA_SECRET_KEY"),
        "cron_secret_configured": _configured("CRON_SECRET"),
        "internal_secrets_configured": _internal_secrets_configured(),
        "stripe_configured": _stripe_configured(),
        "smtp_host_configured": _configured("SMTP_HOST"),
        "smtp_port_configured": _configured("SMTP_PORT"),
        "smtp_username_configured": _configured("SMTP_USERNAME"),
        "smtp_password_configured": _configured("SMTP_PASSWORD"),
        "smtp_from_configured": _configured("SMTP_FROM"),
        "smtp_starttls_configured": _configured("SMTP_STARTTLS"),
        "smtp_configured": _smtp_configured(),
        "google_oauth_configured": _google_oauth_configured(),
        "meta_oauth_configured": _meta_oauth_configured(),
    }


__all__ = ["app", "main"]

if __name__ == "__main__":
    main()
