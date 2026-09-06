from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI
from fastapi.routing import APIRoute

from . import main as _main
from . import store as _store

_REMOTE_BACKENDS = frozenset({"postgres", "turso"})
_POSTGRES_PREFIXES = ("postgres://", "postgresql://")


def storage_backend() -> str:
    """Return the effective storage family without exposing connection details.

    Vercel's PostgreSQL compatibility bootstrap can reuse the legacy
    ``TURSO_DATABASE_URL`` transport variable. Detect the URL scheme so runtime
    diagnostics describe the actual backend instead of the compatibility layer.
    """

    remote_url = (os.getenv("TURSO_DATABASE_URL") or "").strip().lower()
    if remote_url.startswith(_POSTGRES_PREFIXES):
        return "postgres"
    if remote_url:
        return "turso"
    return "sqlite"


def runtime_health_payload() -> dict[str, Any]:
    """Build the existing health payload with backend-safe path reporting."""

    payload = dict(_main.health())
    backend = storage_backend()
    payload["storage_backend"] = backend
    payload["data_path"] = "remote" if backend in _REMOTE_BACKENDS else payload.get("data_path")
    return payload


def install_runtime_diagnostics(app: FastAPI) -> None:
    """Correct the public health route while preserving all existing fields."""

    if getattr(app.state, "vexmera_runtime_diagnostics_installed", False):
        return

    # Keep the shared store helper truthful for code imported after package init,
    # and update main's imported binding used by the legacy health function.
    _store.storage_backend = storage_backend
    _main.storage_backend = storage_backend

    app.router.routes[:] = [
        route
        for route in app.router.routes
        if not (
            isinstance(route, APIRoute)
            and route.path == "/health"
            and "GET" in (route.methods or set())
        )
    ]

    app.add_api_route(
        "/health",
        runtime_health_payload,
        methods=["GET"],
        include_in_schema=False,
        name="health",
    )
    app.state.vexmera_runtime_diagnostics_installed = True
