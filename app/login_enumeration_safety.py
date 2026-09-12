from __future__ import annotations

from typing import Any, Callable

from .auth import hash_password

_DUMMY_PASSWORD = "vexmera-auth-enumeration-dummy"
_DUMMY_SALT = bytes.fromhex("b8c72b6499f162e9f6b7d78bf2a7d3ce")
_GUARD_MARKER = "__vexmera_login_enumeration_guard__"


def _spend_dummy_password_work() -> None:
    """Match the password-KDF work used by a real failed login.

    Login currently returns the same HTTP response for unknown accounts and wrong
    passwords, but an unknown account used to skip PBKDF2 entirely. Spending the
    same password-hash work after a missing account lookup reduces that timing
    signal without creating synthetic users or persisting any extra state.
    """

    hash_password(_DUMMY_PASSWORD, _DUMMY_SALT)


def _wrap_lookup(original: Callable[[str], dict[str, Any] | None]):
    def guarded_get_user_by_email(email: str) -> dict[str, Any] | None:
        user = original(email)
        if user is None:
            _spend_dummy_password_work()
        return user

    setattr(guarded_get_user_by_email, _GUARD_MARKER, True)
    return guarded_get_user_by_email


def install_login_enumeration_safety() -> None:
    """Harden public email lookups used by auth flows against timing enumeration."""

    # Import only after app.main has finished loading. This avoids a circular
    # import while still replacing the module global that the registered route
    # functions resolve at request time.
    from . import main as _main

    current = _main.get_user_by_email
    if getattr(current, _GUARD_MARKER, False):
        return
    _main.get_user_by_email = _wrap_lookup(current)
