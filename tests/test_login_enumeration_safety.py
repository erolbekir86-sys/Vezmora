from __future__ import annotations

from fastapi.routing import APIRoute

import app.main as main_module
from app import login_enumeration_safety as safety


class _LoginRequest:
    def __init__(self, email: str):
        self.email = email


def test_missing_login_user_spends_dummy_password_work(monkeypatch):
    work: list[str] = []
    calls: list[str] = []
    monkeypatch.setattr(safety, "_spend_dummy_password_work", lambda: work.append("pbkdf2"))

    def original(*, request):
        calls.append(str(request.email))
        return {"ok": False}

    guarded = safety._wrap_login_endpoint(original, lambda _email: None)
    request = _LoginRequest("missing@example.com")

    assert guarded(request=request) == {"ok": False}
    assert work == ["pbkdf2"]
    assert calls == ["missing@example.com"]


def test_known_login_user_leaves_real_password_work_to_original(monkeypatch):
    user = {"id": 7, "email": "known@example.com"}
    work: list[str] = []
    monkeypatch.setattr(safety, "_spend_dummy_password_work", lambda: work.append("pbkdf2"))

    guarded = safety._wrap_login_endpoint(lambda **_kwargs: {"ok": True}, lambda _email: user)

    assert guarded(request=_LoginRequest("known@example.com")) == {"ok": True}
    assert work == []


def test_installer_is_scoped_to_login_route_only():
    routes = {
        route.path: route
        for route in main_module.app.routes
        if isinstance(route, APIRoute)
    }

    login_call = routes["/api/auth/login"].dependant.call
    reset_call = routes["/api/auth/password-reset/request"].dependant.call

    assert getattr(login_call, safety._GUARD_MARKER, False) is True
    assert getattr(reset_call, safety._GUARD_MARKER, False) is False


def test_installer_is_idempotent():
    login_route = next(
        route
        for route in main_module.app.routes
        if isinstance(route, APIRoute) and route.path == "/api/auth/login"
    )
    installed = login_route.dependant.call

    safety.install_login_enumeration_safety()

    assert login_route.dependant.call is installed
