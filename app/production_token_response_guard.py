from __future__ import annotations

import os
from functools import wraps
from typing import Any, Callable

from fastapi import FastAPI
from fastapi.routing import APIRoute

_PROTECTED_RESPONSE_FIELDS = {
    "/api/team/invites": frozenset({"invite_token"}),
    "/api/auth/password-reset/request": frozenset({"dev_reset_token"}),
}


def _scrub_result(path: str, result: Any) -> Any:
    if not os.getenv("VERCEL") or not isinstance(result, dict):
        return result
    fields = _PROTECTED_RESPONSE_FIELDS.get(path)
    if not fields:
        return result
    safe = dict(result)
    for field in fields:
        safe.pop(field, None)
    return safe


def _wrap_endpoint(path: str, endpoint: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(endpoint)
    def guarded_endpoint(*args: Any, **kwargs: Any) -> Any:
        return _scrub_result(path, endpoint(*args, **kwargs))

    return guarded_endpoint


def install_production_token_response_guard(app: FastAPI) -> None:
    """Never return raw invite/reset capability tokens from Vercel responses.

    Existing local development behavior is preserved. The guard is installed on
    the already-built APIRoute dependency call so it remains effective even if a
    future code path accidentally adds one of the protected fields again.
    """
    if getattr(app.state, "vexmera_production_token_response_guard_installed", False):
        return

    for route in app.router.routes:
        if not isinstance(route, APIRoute) or route.path not in _PROTECTED_RESPONSE_FIELDS:
            continue
        original = route.dependant.call
        if original is None or getattr(original, "__vexmeraProductionTokenGuard", False):
            continue
        wrapped = _wrap_endpoint(route.path, original)
        wrapped.__vexmeraProductionTokenGuard = True
        route.endpoint = wrapped
        route.dependant.call = wrapped

    app.state.vexmera_production_token_response_guard_installed = True
