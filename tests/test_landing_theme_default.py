from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "static" / "landing-premium.js"


def test_dark_default_preserves_explicit_saved_theme():
    """The dark rollout must not overwrite a visitor's prior explicit choice."""
    source = SCRIPT.read_text(encoding="utf-8")

    assert "const savedTheme = localStorage.getItem('vexmera-theme')" in source
    assert "savedTheme === 'light' || savedTheme === 'dark'" in source
    assert "const theme = hasExplicitTheme ? savedTheme : 'dark'" in source
    assert "if (!hasExplicitTheme) localStorage.setItem('vexmera-theme', theme)" in source


def test_dark_default_remains_fail_safe_when_storage_is_unavailable():
    source = SCRIPT.read_text(encoding="utf-8")

    assert "catch (_)" in source
    assert "document.documentElement.setAttribute('data-theme', 'dark')" in source
    assert "document.documentElement.style.colorScheme = 'dark'" in source
