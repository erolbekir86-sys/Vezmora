from __future__ import annotations

from fastapi.routing import APIRoute

from app.auth import require_user
from app.main import app


# These API routes are intentionally usable without an authenticated product
# session because they have a separate trust boundary or bootstrap auth itself.
# Keeping this list explicit makes any newly-public API route a review event.
PUBLIC_API_PATHS = {
    "/api/auth/register",
    "/api/auth/login",
    "/api/auth/logout",
    "/api/auth/password-reset/request",
    "/api/auth/password-reset/confirm",
    "/api/connectors/google/callback",
    "/api/connectors/meta/callback",
    "/api/billing/webhook",
    "/api/internal/cron/maintenance",
}


def _dependency_calls(dependant):
    for child in dependant.dependencies:
        yield child.call
        yield from _dependency_calls(child)


def test_every_non_public_api_route_requires_product_authentication():
    uncovered: list[str] = []

    for route in app.routes:
        if not isinstance(route, APIRoute) or not route.path.startswith("/api/"):
            continue
        if route.path in PUBLIC_API_PATHS:
            continue
        if require_user not in set(_dependency_calls(route.dependant)):
            methods = ",".join(sorted(route.methods or set()))
            uncovered.append(f"{methods} {route.path}")

    assert uncovered == [], "API routes without product auth: " + "; ".join(uncovered)


def test_public_api_allowlist_only_contains_existing_routes():
    existing = {
        route.path
        for route in app.routes
        if isinstance(route, APIRoute) and route.path.startswith("/api/")
    }
    assert PUBLIC_API_PATHS <= existing
