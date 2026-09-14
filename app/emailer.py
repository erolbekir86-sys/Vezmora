from __future__ import annotations

import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Any
from urllib.parse import urlsplit

from .store import claim_email, finish_email


def smtp_configured() -> bool:
    return bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_FROM"))


def _production_https_origin(value: str) -> str | None:
    """Return a normalized HTTPS origin suitable for capability links."""
    if not value:
        return None
    parts = urlsplit(value)
    if parts.scheme.lower() != "https" or not parts.netloc:
        return None
    if parts.username is not None or parts.password is not None:
        return None
    if parts.path not in {"", "/"} or parts.query or parts.fragment:
        return None
    return f"https://{parts.netloc}"


def app_url() -> str:
    """Return the canonical application origin used in capability emails.

    Local development keeps the historical localhost fallback. Vercel must never
    manufacture password-reset or workspace-invite links from that fallback or
    from a configured URL containing credentials, path, query string, or fragment.
    """
    configured = (os.getenv("VEZMORA_APP_URL") or "").strip()
    if os.getenv("VERCEL"):
        origin = _production_https_origin(configured)
        if origin is None:
            raise RuntimeError("VEZMORA_APP_URL must be configured as a plain HTTPS origin on Vercel")
        return origin
    return configured.rstrip("/") or "http://localhost:8000"


def _smtp_starttls_enabled() -> bool:
    return os.getenv("SMTP_STARTTLS", "true").strip().lower() in {"1", "true", "yes", "on"}


def send_email(recipient: str, subject: str, body: str) -> None:
    host = (os.getenv("SMTP_HOST") or "").strip()
    sender = (os.getenv("SMTP_FROM") or "").strip()
    if not host or not sender:
        raise RuntimeError("SMTP is not configured")

    try:
        port = int((os.getenv("SMTP_PORT") or "587").strip())
    except ValueError as exc:
        raise RuntimeError("SMTP_PORT is invalid") from exc
    if not 1 <= port <= 65535:
        raise RuntimeError("SMTP_PORT is invalid")

    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    use_tls = _smtp_starttls_enabled()

    # Vercel is the production deployment boundary for the private beta. Never
    # transmit invite/reset content or SMTP credentials over plaintext transport
    # there, even if a stale environment override disables STARTTLS.
    if os.getenv("VERCEL") and not use_tls:
        raise RuntimeError("SMTP STARTTLS is required on Vercel")

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(host, port, timeout=20) as smtp:
        if use_tls:
            smtp.starttls(context=ssl.create_default_context())
        if username and password:
            smtp.login(username, password)
        smtp.send_message(msg)


def run_email_once() -> bool:
    row = claim_email()
    if not row:
        return False
    try:
        send_email(str(row["recipient"]), str(row["subject"]), str(row["body_text"]))
        finish_email(int(row["id"]))
    except Exception as exc:
        finish_email(int(row["id"]), f"{type(exc).__name__}: {exc}")
    return True
