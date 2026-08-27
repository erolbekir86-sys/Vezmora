from __future__ import annotations

import asyncio
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

from app.agent import generate_campaign, generate_strategy, run_agent
from app.main import app, main
from app.models import AgentRequest, CampaignRequest, CompanyProfile, StrategyRequest


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


_PRODUCT_SMOKE_CACHE: dict[str, object] | None = None


def _error_metadata(value: object) -> dict[str, object]:
    """Return only non-secret OpenAI error metadata, never messages or request bodies."""
    if not isinstance(value, BaseException):
        return {"error": None, "error_code": None, "error_type": None, "status_code": None}

    code = getattr(value, "code", None)
    error_type = getattr(value, "type", None)
    status_code = getattr(value, "status_code", None)
    body = getattr(value, "body", None)
    if isinstance(body, dict):
        nested = body.get("error") if isinstance(body.get("error"), dict) else body
        if isinstance(nested, dict):
            code = code or nested.get("code")
            error_type = error_type or nested.get("type")

    return {
        "error": type(value).__name__,
        "error_code": str(code) if code else None,
        "error_type": str(error_type) if error_type else None,
        "status_code": int(status_code) if isinstance(status_code, int) else None,
    }


async def _product_smoke() -> dict[str, object]:
    """Run fixed, non-user-controlled calls through the three core AI pipelines."""
    global _PRODUCT_SMOKE_CACHE
    if _PRODUCT_SMOKE_CACHE is not None:
        return _PRODUCT_SMOKE_CACHE

    company = CompanyProfile(
        name="Vexmera Smoke Test",
        industry="Local services",
        market="Sweden",
        audience="Local customers looking for a reliable home service",
        offer="Reliable service with clear pricing and fast booking",
        brand_voice="clear, trustworthy, useful",
        language="en",
    )
    memory: dict[str, object] = {}
    calls = [
        (
            "core",
            lambda: run_agent(
                AgentRequest(
                    company=company,
                    message="Production health smoke test. Give one concise strategic marketing recommendation and do not propose any external execution.",
                ),
                memory,
            ),
        ),
        (
            "pulse",
            lambda: generate_strategy(
                StrategyRequest(
                    company=company,
                    objective="leads",
                    budget_sek=1000,
                    horizon_days=7,
                    notes="Production smoke test. Keep the answer concise and do not execute anything.",
                ),
                memory,
            ),
        ),
        (
            "launch",
            lambda: generate_campaign(
                CampaignRequest(
                    company=company,
                    objective="leads",
                    channel="organic",
                    campaign_name="Production Smoke Test",
                    budget_sek=0,
                    notes="Production smoke test. Keep the answer concise and do not execute anything.",
                ),
                memory,
            ),
        ),
    ]

    results: dict[str, object] = {}
    for index, (name, factory) in enumerate(calls):
        try:
            results[name] = await factory()
        except Exception as exc:
            results[name] = exc
        if index < len(calls) - 1:
            # Avoid an artificial request burst while diagnosing low-tier rate limits.
            await asyncio.sleep(2.0)

    def ok(value: object) -> bool:
        return isinstance(value, str) and len(value.strip()) >= 20

    payload: dict[str, object] = {}
    all_ok = True
    for name in ("core", "pulse", "launch"):
        value = results[name]
        passed = ok(value)
        all_ok = all_ok and passed
        meta = _error_metadata(value)
        payload[f"{name}_smoke_ok"] = passed
        payload[f"{name}_smoke_error"] = meta["error"]
        payload[f"{name}_smoke_error_code"] = meta["error_code"]
        payload[f"{name}_smoke_error_type"] = meta["error_type"]
        payload[f"{name}_smoke_status_code"] = meta["status_code"]

    payload["product_smoke_ok"] = all_ok
    _PRODUCT_SMOKE_CACHE = payload
    return _PRODUCT_SMOKE_CACHE


@app.get("/health/runtime")
async def runtime_diagnostics(deep: bool = False) -> dict[str, object]:
    """Expose only non-secret deployment diagnostics for production debugging."""
    result: dict[str, object] = {
        "ok": True,
        "brand": "Vexmera",
        "vercel": bool(os.getenv("VERCEL")),
        "vercel_env": os.getenv("VERCEL_ENV") or None,
        "git_commit_sha": os.getenv("VERCEL_GIT_COMMIT_SHA") or None,
        "database_url_configured": bool((os.getenv("DATABASE_URL") or "").strip()),
        "postgres_url_configured": bool((os.getenv("POSTGRES_URL") or "").strip()),
        "remote_store_configured": bool((os.getenv("TURSO_DATABASE_URL") or "").strip()),
        "database_connection_ok": _database_connection_ok(),
        "openai_api_key_configured": bool((os.getenv("OPENAI_API_KEY") or "").strip()),
        "openai_connection_ok": _openai_connection_ok(),
        "openai_model_configured": bool((os.getenv("OPENAI_MODEL") or "").strip()),
        "serverless_configured": (os.getenv("VEZMORA_SERVERLESS") or "").lower() in {"1", "true", "yes", "on"},
    }
    if deep:
        result["deep_smoke_test_ran"] = True
        result.update(await _product_smoke())
    return result


__all__ = ["app", "main"]

if __name__ == "__main__":
    main()
