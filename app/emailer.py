from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import Any

from .store import claim_email, finish_email


def smtp_configured() -> bool:
    return bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_FROM"))


def app_url() -> str:
    return os.getenv("VEZMORA_APP_URL", "http://localhost:8000").rstrip("/")


def send_email(recipient: str, subject: str, body: str) -> None:
    host = os.getenv("SMTP_HOST")
    sender = os.getenv("SMTP_FROM")
    if not host or not sender:
        raise RuntimeError("SMTP is not configured")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    use_tls = os.getenv("SMTP_STARTTLS", "true").lower() in {"1", "true", "yes", "on"}

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(host, port, timeout=20) as smtp:
        if use_tls:
            smtp.starttls()
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
