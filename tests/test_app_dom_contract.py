from __future__ import annotations

import re
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
APP = (ROOT / "static" / "app.js").read_text(encoding="utf-8")


def test_every_literal_app_dom_id_exists_or_is_created_by_app_runtime():
    referenced = set(re.findall(r"\$\(['\"]([^'\"]+)['\"]\)", APP))
    referenced.update(re.findall(r"getElementById\(['\"]([^'\"]+)['\"]\)", APP))

    declared = set(re.findall(r"\bid=['\"]([^'\"]+)['\"]", INDEX))
    dynamically_created = set(re.findall(r"\bid=[\\\"']([^\\\"']+)[\\\"']", APP))

    missing = sorted(referenced - declared - dynamically_created)
    assert not missing, f"app.js references DOM ids that are neither shipped nor created at runtime: {missing}"


def test_product_shell_keeps_auth_visible_until_app_bootstrap_succeeds():
    assert 'id="authScreen" class="auth-screen"' in INDEX
    assert 'id="appShell" class="shell hidden"' in INDEX
    assert "async function bootstrap()" in APP
    assert "if(err.status===401)showAuth()" in APP


def test_product_shell_uses_stability_first_polish_runtime():
    with TestClient(app) as client:
        page = client.get('/app')
        safe_polish = client.get('/static/app-polish-safe.js')

    assert page.status_code == 200
    assert safe_polish.status_code == 200
    assert '/static/app-polish-safe.js?build=' in page.text
    assert '/static/app-polish.js' not in page.text
    assert 'new MutationObserver(' not in safe_polish.text
    assert 'dataset.vexmeraAppPolishStable' in safe_polish.text
