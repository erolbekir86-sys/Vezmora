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
