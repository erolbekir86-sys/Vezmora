from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
APP_JS = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
POLISH_CSS = (ROOT / "static" / "app-polish.css").read_text(encoding="utf-8")
POLISH_JS = (ROOT / "static" / "app-polish.js").read_text(encoding="utf-8")


def test_command_center_loads_polish_assets():
    assert '/static/app-polish.css?v=1' in INDEX
    assert '/static/app-polish.js?v=1' in INDEX
    assert 'AI-DRIVEN MARKETING INTELLIGENCE' in INDEX
    assert 'AUTONOMOUS MARKETING INTELLIGENCE' not in INDEX


def test_command_center_pricing_matches_marketing_site():
    assert '<strong>1 499 kr</strong>' in INDEX
    assert '<strong>2 999 kr</strong>' in INDEX
    assert '<strong>5 999 kr</strong>' in INDEX
    assert '<strong>499 kr</strong>' not in INDEX
    assert '<strong>3 999 kr+</strong>' not in INDEX


def test_core_product_ids_are_preserved_for_existing_app_logic():
    required_ids = (
        'authScreen', 'appShell', 'workspaceSelect', 'language', 'dashboard',
        'agent', 'strategy', 'campaign', 'brief', 'queue', 'autopilot',
        'rivals', 'connect', 'insights', 'team', 'profile', 'aiOutputSection',
        'onboardingModal', 'resetModal', 'metricRevenue', 'connectorGrid',
        'approvalList', 'autopilotRuntime', 'billingStatus',
    )
    for element_id in required_ids:
        assert f'id="{element_id}"' in INDEX


def test_every_literal_app_js_dom_id_still_exists_in_index():
    # app.js uses the tiny $("id") helper as its DOM contract. Rebuilding the
    # customer-facing HTML must never silently remove an element the product uses.
    referenced_ids = set(re.findall(r"\$\(['\"]([A-Za-z0-9_-]+)['\"]\)", APP_JS))
    missing = sorted(element_id for element_id in referenced_ids if f'id="{element_id}"' not in INDEX)
    assert not missing, f"Missing DOM ids required by app.js: {missing}"


def test_polish_keeps_private_beta_messaging_and_reduced_motion():
    assert 'Privat beta' in INDEX
    assert 'prefers-reduced-motion' in POLISH_CSS
    assert 'window.alert = (message) => toast(message)' in POLISH_JS
    assert 'Autonoma högriskåtgärder' in POLISH_JS
