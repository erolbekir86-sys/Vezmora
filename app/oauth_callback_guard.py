from __future__ import annotations

import re

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

OAUTH_STATE_MAX_LENGTH = 128
OAUTH_CODE_MAX_LENGTH = 4096
_OAUTH_STATE_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_CALLBACK_PATHS = frozenset({
    "/api/connectors/google/callback",
    "/api/connectors/google/callback/",
    "/api/connectors/meta/callback",
    "/api/connectors/meta/callback/",
})


def _invalid_callback_input(request: Request) -> str | None:
    if request.method.upper() != "GET" or request.url.path not in _CALLBACK_PATHS:
        return None

    state = request.query_params.get("state")
    code = request.query_params.get("code")

    # Missing required query parameters remain FastAPI's responsibility so the
    # existing 422 contract is preserved. This guard only bounds supplied input.
    if state is not None:
        if not state or len(state) > OAUTH_STATE_MAX_LENGTH or not _OAUTH_STATE_RE.fullmatch(state):
            return "Invalid OAuth state format"
    if code is not None and (not code or len(code) > OAUTH_CODE_MAX_LENGTH):
        return "Invalid OAuth authorization code"
    return None


def install_oauth_callback_guard(app: FastAPI) -> None:
    """Reject malformed/oversized OAuth callback values before DB/provider work."""
    if getattr(app.state, "vexmera_oauth_callback_guard_installed", False):
        return

    @app.middleware("http")
    async def oauth_callback_input_guard(request: Request, call_next):
        detail = _invalid_callback_input(request)
        if detail:
            return JSONResponse(
                status_code=400,
                content={"detail": detail},
                headers={"Cache-Control": "no-store"},
            )
        return await call_next(request)

    app.state.vexmera_oauth_callback_guard_installed = True
