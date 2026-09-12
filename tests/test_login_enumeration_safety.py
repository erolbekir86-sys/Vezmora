from __future__ import annotations

import app.main as main_module
from app import login_enumeration_safety as safety


def test_missing_user_lookup_spends_dummy_password_work(monkeypatch):
    work: list[str] = []
    monkeypatch.setattr(safety, "_spend_dummy_password_work", lambda: work.append("pbkdf2"))
    guarded = safety._wrap_lookup(lambda _email: None)

    assert guarded("missing@example.com") is None
    assert work == ["pbkdf2"]


def test_known_user_lookup_does_not_add_dummy_password_work(monkeypatch):
    user = {"id": 7, "email": "known@example.com"}
    work: list[str] = []
    monkeypatch.setattr(safety, "_spend_dummy_password_work", lambda: work.append("pbkdf2"))
    guarded = safety._wrap_lookup(lambda _email: user)

    assert guarded("known@example.com") is user
    assert work == []


def test_installer_wraps_main_lookup_once(monkeypatch):
    work: list[str] = []
    monkeypatch.setattr(safety, "_spend_dummy_password_work", lambda: work.append("pbkdf2"))
    monkeypatch.setattr(main_module, "get_user_by_email", lambda _email: None)

    safety.install_login_enumeration_safety()
    installed = main_module.get_user_by_email
    safety.install_login_enumeration_safety()

    assert main_module.get_user_by_email is installed
    assert installed("missing@example.com") is None
    assert work == ["pbkdf2"]
