from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from fastapi.routing import APIRoute

from . import store as _store
from .auth import hash_password

_DUMMY_PASSWORD = "vexmera-auth-enumeration-dummy"
_DUMMY_SALT = bytes.fromhex("b8c72b6499f162e9f6b7d78bf2a7d3ce")
_GUARD_MARKER = "__vexmera_login_enumeration_guard__"
_LOGIN_PATH = "/api/auth/login"
_CURRENT_PASSWORD_PREFIX = "pbkdf2_sha256$"


def _spend_dummy_password_work() -> None:
    """Match the password-KDF work used by a real failed login."""

    hash_password(_DUMMY_PASSWORD, _DUMMY_SALT)


def _is_legacy_password_record(user: dict[str, Any] | None) -> bool:
    if not user:
        return False
    salt_record = str(user.get("password_salt") or "")
    return bool(salt_record) and not salt_record.startswith(_CURRENT_PASSWORD_PREFIX)


def _upgrade_legacy_password_record(user: dict[str, Any], password: str) -> None:
    """Best-effort compare-and-set rehash without revoking existing sessions.

    A successful login has already verified the legacy credential before this
    helper runs. The conditional UPDATE prevents a concurrent password reset or
    credential change from being overwritten. Rehash failure must never turn a
    valid login into an outage; the next successful login can retry migration.
    """

    old_salt = str(user.get("password_salt") or "")
    old_hash = str(user.get("password_hash") or "")
    if not old_salt or not old_hash:
        return

    new_salt, new_hash = hash_password(password)
    try:
        with _store._connect() as con:
            con.execute(
                """UPDATE users
                   SET password_salt=?, password_hash=?
                   WHERE id=? AND password_salt=? AND password_hash=?""",
                (new_salt, new_hash, int(user["id"]), old_salt, old_hash),
            )
    except Exception:
        # Migration is opportunistic. Authentication has already succeeded and
        # must not fail only because this defense-in-depth write could not run.
        return


def _wrap_login_endpoint(
    original: Callable[..., Any],
    lookup_user: Callable[[str], dict[str, Any] | None],
) -> Callable[..., Any]:
    """Equalize account timing and upgrade legacy KDF records after valid login.

    FastAPI has already parsed the LoginRequest before invoking this callable.
    A missing account gets one dummy current-policy PBKDF2 operation before the
    unchanged login endpoint runs. Known legacy accounts are rehashed only after
    the original endpoint returns successfully, so a wrong password can never
    trigger credential migration. Password-reset flows remain untouched.
    """

    @wraps(original)
    def guarded_login(*args: Any, **kwargs: Any) -> Any:
        login_request = kwargs.get("request")
        email = getattr(login_request, "email", None)
        user = lookup_user(str(email)) if email is not None else None
        if email is not None and user is None:
            _spend_dummy_password_work()

        result = original(*args, **kwargs)

        if user is not None and _is_legacy_password_record(user):
            password = getattr(login_request, "password", None)
            if isinstance(password, str):
                _upgrade_legacy_password_record(user, password)
        return result

    setattr(guarded_login, _GUARD_MARKER, True)
    return guarded_login


def install_login_enumeration_safety() -> None:
    """Reduce login account enumeration and migrate legacy hashes on success."""

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
