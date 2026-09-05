from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .google_ads_diagnostics import _redact_sensitive_text


def sanitize_http_detail(value: Any) -> Any:
    """Redact credential-like text while preserving FastAPI's error shape."""
    if isinstance(value, str):
        return _redact_sensitive_text(value)
    if isinstance(value, Mapping):
        return {str(key): sanitize_http_detail(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [sanitize_http_detail(item) for item in value]
    return value


def install_http_error_safety(app: FastAPI) -> None:
    """Install a defense-in-depth HTTPException handler for user-visible errors."""

    @app.exception_handler(HTTPException)
    async def _safe_http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        del request
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": sanitize_http_detail(exc.detail)},
            headers=exc.headers,
        )
