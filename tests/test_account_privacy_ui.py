from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_authenticated_app_loads_account_privacy_ui():
    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    assert '<script src="/static/account-privacy-ui.js?v=1"></script>' in html
    assert html.index('/static/app-polish.js?v=1') < html.index('/static/account-privacy-ui.js?v=1')


def test_account_privacy_ui_uses_guarded_backend_flow():
    js = (ROOT / "static" / "account-privacy-ui.js").read_text(encoding="utf-8")
    assert "/api/privacy/account-deletion-preview" in js
    assert "/api/privacy/account" in js
    assert "DELETE MY ACCOUNT" in js
    assert 'autocomplete="current-password"' in js
    assert "preview?.allowed" in js
    assert "window.confirm" in js
    assert "method: 'DELETE'" in js


def test_account_privacy_ui_explains_blockers_and_processor_retention():
    js = (ROOT / "static" / "account-privacy-ui.js").read_text(encoding="utf-8")
    assert "Överför ägarskapet eller ta bort övriga medlemmar först." in js
    assert "Avsluta den aktiva Stripe-prenumerationen först." in js
    assert "Externa bokförings- eller betalningsuppgifter" in js
