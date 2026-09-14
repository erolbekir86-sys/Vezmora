from __future__ import annotations

import ssl

import pytest

from app import emailer


class _FakeSMTP:
    instances = []

    def __init__(self, host, port, timeout):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.starttls_context = None
        self.login_args = None
        self.sent = None
        self.__class__.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def starttls(self, *, context=None):
        self.starttls_context = context
        return (220, b"ready")

    def login(self, username, password):
        self.login_args = (username, password)

    def send_message(self, msg):
        self.sent = msg


def _configure(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.test")
    monkeypatch.setenv("SMTP_FROM", "noreply@example.test")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USERNAME", "user")
    monkeypatch.setenv("SMTP_PASSWORD", "password")


def test_vercel_requires_plain_https_canonical_app_url_for_capability_links(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")

    invalid_values = [
        None,
        "http://vexmera.example",
        "https://user:secret@vexmera.example",
        "https://vexmera.example/app",
        "https://vexmera.example?next=reset",
        "https://vexmera.example#invite",
    ]

    for value in invalid_values:
        if value is None:
            monkeypatch.delenv("VEZMORA_APP_URL", raising=False)
        else:
            monkeypatch.setenv("VEZMORA_APP_URL", value)
        with pytest.raises(RuntimeError, match="plain HTTPS origin"):
            emailer.app_url()

    monkeypatch.setenv("VEZMORA_APP_URL", "https://vexmera.example/")
    assert emailer.app_url() == "https://vexmera.example"


def test_local_development_keeps_localhost_fallback(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("VEZMORA_APP_URL", raising=False)
    assert emailer.app_url() == "http://localhost:8000"


def test_local_configured_origin_keeps_existing_trailing_slash_normalization(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv("VEZMORA_APP_URL", "https://local-preview.example///")
    assert emailer.app_url() == "https://local-preview.example"


def test_vercel_refuses_plaintext_smtp(monkeypatch):
    _FakeSMTP.instances.clear()
    _configure(monkeypatch)
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("SMTP_STARTTLS", "false")
    monkeypatch.setattr(emailer.smtplib, "SMTP", _FakeSMTP)

    with pytest.raises(RuntimeError, match="STARTTLS is required"):
        emailer.send_email("person@example.test", "Subject", "Body")

    assert _FakeSMTP.instances == []


def test_starttls_uses_verifying_default_ssl_context(monkeypatch):
    _FakeSMTP.instances.clear()
    _configure(monkeypatch)
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("SMTP_STARTTLS", "true")
    monkeypatch.setattr(emailer.smtplib, "SMTP", _FakeSMTP)

    emailer.send_email("person@example.test", "Subject", "Body")

    smtp = _FakeSMTP.instances[-1]
    assert isinstance(smtp.starttls_context, ssl.SSLContext)
    assert smtp.starttls_context.verify_mode == ssl.CERT_REQUIRED
    assert smtp.starttls_context.check_hostname is True
    assert smtp.login_args == ("user", "password")
    assert smtp.sent["To"] == "person@example.test"


def test_invalid_smtp_port_fails_before_network(monkeypatch):
    _FakeSMTP.instances.clear()
    _configure(monkeypatch)
    monkeypatch.setenv("SMTP_PORT", "70000")
    monkeypatch.setattr(emailer.smtplib, "SMTP", _FakeSMTP)

    with pytest.raises(RuntimeError, match="SMTP_PORT is invalid"):
        emailer.send_email("person@example.test", "Subject", "Body")

    assert _FakeSMTP.instances == []
