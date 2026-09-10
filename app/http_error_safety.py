from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .secret_redaction import redact_sensitive_text


def sanitize_http_detail(value: Any) -> Any:
    """Redact credential-like text while preserving FastAPI's error shape."""
    if isinstance(value, str):
        return redact_sensitive_text(value)
    if isinstance(value, Mapping):
        return {str(key): sanitize_http_detail(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [sanitize_http_detail(item) for item in value]
    return value


def install_http_error_safety(app: FastAPI) -> None:
    """Install defense-in-depth handlers for user-visible/provider transport errors."""

    @app.exception_handler(HTTPException)
    async def _safe_http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        del request
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": sanitize_http_detail(exc.detail)},
            headers=exc.headers,
        )

    @app.exception_handler(httpx.TransportError)
    async def _safe_transport_error_handler(request: Request, exc: httpx.TransportError) -> JSONResponse:
        # httpx transport exceptions may stringify a request URL. Provider URLs
        # can contain OAuth access tokens in query parameters, so neither the raw
        # exception nor request details belong in a customer-visible response.
        del request, exc
        return JSONResponse(
            status_code=502,
            content={"detail": "Upstream provider connection failed. Try again later."},
            headers={"Cache-Control": "no-store"},
        )
