from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAFE_JS = (ROOT / "static" / "app-polish-safe.js").read_text(encoding="utf-8")
AUTH_CSS = (ROOT / "static" / "auth-contrast.css").read_text(encoding="utf-8")


def test_safe_runtime_loads_auth_contrast_layer():
    assert "/static/auth-contrast.css" in SAFE_JS
    assert "data-vexmera-auth-contrast" in SAFE_JS


def test_auth_screen_stays_dark_even_with_light_theme():
    assert 'html[data-vex-theme="light"] .auth-screen' in AUTH_CSS
    assert "#0a0e14" in AUTH_CSS


def test_auth_copy_uses_high_contrast_brand_palette():
    assert ".auth-card h1" in AUTH_CSS
    assert "#f0d7aa" in AUTH_CSS
    assert ".auth-card .lead" in AUTH_CSS
    assert "#c7ced8" in AUTH_CSS
    assert ".auth-form label" in AUTH_CSS
    assert "#d7dde5" in AUTH_CSS


def test_auth_inputs_are_dark_and_readable():
    assert "background:#121821!important" in AUTH_CSS
    assert "color:#f3f6f9!important" in AUTH_CSS
    assert "border-color:#c7a56c!important" in AUTH_CSS
