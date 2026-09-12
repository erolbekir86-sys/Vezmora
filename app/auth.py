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
PBKDF2_ITERATIONS = 600_000
LEGACY_PBKDF2_ITERATIONS = 310_000
_PASSWORD_SCHEME = "pbkdf2_sha256"


def _derive_password(password: str, salt: bytes, iterations: int) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)


def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    """Create a self-describing PBKDF2-SHA256 password record.

    New credentials use the current 600k work factor. Historical Vexmera rows
    stored only a hexadecimal salt and are still accepted by ``verify_password``.
    Encoding the scheme/work factor in the salt column makes future upgrades
    possible without a database migration or account lockout.
    """
    salt = salt or secrets.token_bytes(16)
    digest = _derive_password(password, salt, PBKDF2_ITERATIONS)
    salt_record = f"{_PASSWORD_SCHEME}${PBKDF2_ITERATIONS}${salt.hex()}"
    return salt_record, digest.hex()


def _parse_password_salt(value: str) -> tuple[bytes, int, bool] | None:
    """Return salt, work factor and legacy marker for a supported record."""
    try:
        if value.startswith(f"{_PASSWORD_SCHEME}$"):
            scheme, raw_iterations, salt_hex = value.split("$", 2)
            if scheme != _PASSWORD_SCHEME:
                return None
            iterations = int(raw_iterations)
            if iterations != PBKDF2_ITERATIONS:
                return None
            salt = bytes.fromhex(salt_hex)
            return (salt, iterations, False) if salt else None

        # Pre-upgrade rows contain only the 16-byte salt as hexadecimal text.
        salt = bytes.fromhex(value)
        return (salt, LEGACY_PBKDF2_ITERATIONS, True) if salt else None
    except (AttributeError, TypeError, ValueError):
        return None


def _pad_legacy_verification(salt: bytes) -> None:
    """Keep legacy verification near the current KDF cost before comparison.

    This preserves the login timing hardening: unknown accounts spend the current
    600k KDF work, current records spend 600k, and legacy records spend their old
    310k verification plus 290k of non-secret padding work.
    """
    remaining = PBKDF2_ITERATIONS - LEGACY_PBKDF2_ITERATIONS
    if remaining > 0:
        hashlib.pbkdf2_hmac("sha256", b"vexmera-legacy-kdf-padding", salt, remaining)


def verify_password(password: str, salt_record: str, expected_hex: str) -> bool:
    """Verify current and legacy credentials while malformed rows fail closed."""
    parsed = _parse_password_salt(salt_record)
    if parsed is None:
        return False
    salt, iterations, legacy = parsed
    try:
        expected = bytes.fromhex(expected_hex)
    except (TypeError, ValueError):
        return False
    if len(expected) != hashlib.sha256().digest_size:
        return False

    digest = _derive_password(password, salt, iterations)
    if legacy:
        _pad_legacy_verification(salt)
    return hmac.compare_digest(digest, expected)


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
