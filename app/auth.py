from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Cookie, HTTPException, Response

from .store import create_session, get_session_user, revoke_session

SESSION_COOKIE = "vezmora_session"
SESSION_DAYS = 14
SESSION_TOKEN_MAX_LENGTH = 128


def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310_000)
    return salt.hex(), digest.hex()


def verify_password(password: str, salt_hex: str, expected_hex: str) -> bool:
    """Verify credentials without turning malformed stored hashes into a 500."""
    try:
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(expected_hex)
    except (TypeError, ValueError):
        return False
    if not salt or len(expected) != hashlib.sha256().digest_size:
        return False
    _, digest_hex = hash_password(password, salt)
    return hmac.compare_digest(digest_hex, expected.hex())


def _secure_cookie() -> bool:
    # Vercel production/preview deployments are HTTPS. Never allow a stale or
    # mistaken VEZMORA_COOKIE_SECURE=false override to weaken auth cookies there.
    if os.getenv("VERCEL"):
        return True
    configured = os.getenv("VEZMORA_COOKIE_SECURE")
    if configured is not None:
        return configured.lower() in {"1", "true", "yes", "on"}
    return (os.getenv("VEZMORA_APP_URL") or "").lower().startswith("https://")


def _session_token_hash(raw_token: str | None) -> str | None:
    """Hash only plausible session-cookie input and fail closed otherwise."""
    if not raw_token or len(raw_token) > SESSION_TOKEN_MAX_LENGTH:
        return None
    try:
        encoded = raw_token.encode("ascii")
    except UnicodeEncodeError:
        return None
    return hashlib.sha256(encoded).hexdigest()


def start_session(response: Response, user_id: int) -> None:
    raw = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    create_session(user_id, token_hash, expires_at.isoformat())
    response.set_cookie(
        SESSION_COOKIE,
        raw,
        max_age=SESSION_DAYS * 24 * 3600,
        httponly=True,
        secure=_secure_cookie(),
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    """Expire the auth cookie with the same attributes used when it is created."""
    response.delete_cookie(
        SESSION_COOKIE,
        path="/",
        httponly=True,
        secure=_secure_cookie(),
        samesite="lax",
    )


def end_session(response: Response, raw_token: str | None) -> None:
    token_hash = _session_token_hash(raw_token)
    if token_hash:
        revoke_session(token_hash)
    clear_session_cookie(response)


def require_user(vezmora_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    if not vezmora_session:
        raise HTTPException(status_code=401, detail="Authentication required")
    token_hash = _session_token_hash(vezmora_session)
    if not token_hash:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    user = get_session_user(token_hash)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    return user
