from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
APP = (ROOT / "static" / "app.js").read_text(encoding="utf-8")


def test_every_literal_app_dom_id_exists_in_product_shell():
    referenced = set(re.findall(r"\$\(['\"]([^'\"]+)['\"]\)", APP))
    referenced.update(re.findall(r"getElementById\(['\"]([^'\"]+)['\"]\)", APP))
    declared = set(re.findall(r"\bid=['\"]([^'\"]+)['\"]", INDEX))

    missing = sorted(referenced - declared)
    assert not missing, f"app.js references DOM ids missing from static/index.html: {missing}"


def test_product_shell_keeps_auth_visible_until_app_bootstrap_succeeds():
    assert 'id="authScreen" class="auth-screen"' in INDEX
    assert 'id="appShell" class="shell hidden"' in INDEX
    assert "async function bootstrap()" in APP
    assert "if(err.status===401)showAuth()" in APP
