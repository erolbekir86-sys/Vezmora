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


def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310_000)
    return salt.hex(), digest.hex()


def verify_password(password: str, salt_hex: str, expected_hex: str) -> bool:
    salt = bytes.fromhex(salt_hex)
    _, digest_hex = hash_password(password, salt)
    return hmac.compare_digest(digest_hex, expected_hex)


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
        secure=os.getenv("VEZMORA_COOKIE_SECURE", "false").lower() == "true",
        samesite="lax",
        path="/",
    )


def end_session(response: Response, raw_token: str | None) -> None:
    if raw_token:
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        revoke_session(token_hash)
    response.delete_cookie(SESSION_COOKIE, path="/")


def require_user(vezmora_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    if not vezmora_session:
        raise HTTPException(status_code=401, detail="Authentication required")
    token_hash = hashlib.sha256(vezmora_session.encode("utf-8")).hexdigest()
    user = get_session_user(token_hash)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    return user
