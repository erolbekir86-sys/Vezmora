from __future__ import annotations

import os
import re

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

_EXECUTION_RUN_RE = re.compile(r"^/api/executions/\d+/run/?$")
_AUTOPILOT_RUN_PATHS = frozenset({"/api/autopilot/run-once", "/api/autopilot/run-once/"})


def _is_blocked_execution_request(request: Request) -> bool:
    if request.method.upper() != "POST":
        return False
    path = request.url.path
    return bool(_EXECUTION_RUN_RE.fullmatch(path)) or path in _AUTOPILOT_RUN_PATHS


def install_production_execution_guard(app: FastAPI) -> None:
    """Hard-lock external execution endpoints on Vercel during Private Beta.

    This is intentionally independent of runtime environment feature flags. The
    lower-level execution helpers also fail closed on Vercel, so an accidental
    future flag change cannot make the production mutation endpoints executable.
    Preview/read endpoints remain available for human review.
    """
    if getattr(app.state, "vexmera_production_execution_guard_installed", False):
        return

    @app.middleware("http")
    async def production_execution_guard(request: Request, call_next):
        if os.getenv("VERCEL") and _is_blocked_execution_request(request):
            return JSONResponse(
                status_code=409,
                content={
                    "detail": "External execution is disabled in Vexmera Private Beta. Review and recommendation features remain available."
                },
                headers={"Cache-Control": "no-store"},
            )
        return await call_next(request)

    app.state.vexmera_production_execution_guard_installed = True
