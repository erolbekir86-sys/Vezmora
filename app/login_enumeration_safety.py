from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from fastapi.routing import APIRoute

from .auth import hash_password

_DUMMY_PASSWORD = "vexmera-auth-enumeration-dummy"
_DUMMY_SALT = bytes.fromhex("b8c72b6499f162e9f6b7d78bf2a7d3ce")
_GUARD_MARKER = "__vexmera_login_enumeration_guard__"
_LOGIN_PATH = "/api/auth/login"


def _spend_dummy_password_work() -> None:
    """Match the password-KDF work used by a real failed login."""

    hash_password(_DUMMY_PASSWORD, _DUMMY_SALT)


def _wrap_login_endpoint(
    original: Callable[..., Any],
    lookup_user: Callable[[str], dict[str, Any] | None],
) -> Callable[..., Any]:
    """Equalize the obvious known-vs-unknown account work for login only.

    FastAPI has already parsed the LoginRequest before invoking this callable.
    A missing account gets one dummy PBKDF2 operation before the unchanged login
    endpoint runs. A known account reaches the endpoint's real password verify.
    Password-reset and other email lookups are intentionally untouched.
    """

    @wraps(original)
    def guarded_login(*args: Any, **kwargs: Any) -> Any:
        login_request = kwargs.get("request")
        email = getattr(login_request, "email", None)
        if email is not None and lookup_user(str(email)) is None:
            _spend_dummy_password_work()
        return original(*args, **kwargs)

    setattr(guarded_login, _GUARD_MARKER, True)
    return guarded_login


def install_login_enumeration_safety() -> None:
    """Reduce login account-enumeration timing without touching reset flows."""

    from . import main as _main

    for route in _main.app.router.routes:
        if not isinstance(route, APIRoute) or route.path != _LOGIN_PATH:
            continue
        original = route.dependant.call
        if original is None or getattr(original, _GUARD_MARKER, False):
            return
        wrapped = _wrap_login_endpoint(original, _main.get_user_by_email)
        route.endpoint = wrapped
        route.dependant.call = wrapped
        return
