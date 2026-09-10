from __future__ import annotations

import os

from fastapi import FastAPI, Request


def _https_runtime() -> bool:
    if (os.getenv("VERCEL") or "").strip():
        return True
    return (os.getenv("VEZMORA_APP_URL") or "").strip().lower().startswith("https://")


def install_security_headers(app: FastAPI) -> None:
    """Add browser hardening headers without changing application routing or CSP."""

    @app.middleware("http")
    async def _security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")
        if _https_runtime():
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
        return response
