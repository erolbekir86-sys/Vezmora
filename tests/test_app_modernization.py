from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAFE_JS = (ROOT / "static" / "app-polish-safe.js").read_text(encoding="utf-8")
MODERN_CSS = (ROOT / "static" / "app-modern.css").read_text(encoding="utf-8")


def test_safe_runtime_loads_modern_visual_layer_without_global_observer():
    assert "/static/app-modern.css" in SAFE_JS
    assert "MutationObserver(" not in SAFE_JS
    assert "vexmeraAppPolishStable" in SAFE_JS


def test_theme_is_persistent_and_supports_light_and_dark_modes():
    assert "vexmera-theme" in SAFE_JS
    assert "localStorage.getItem" in SAFE_JS
    assert "localStorage.setItem" in SAFE_JS
    assert 'data-vex-theme="light"' in MODERN_CSS
    assert 'data-vex-theme="dark"' in MODERN_CSS


def test_navigation_and_kpi_visual_semantics_are_present():
    assert "vex-nav-icon" in SAFE_JS
    assert "vex-metric-icon" in SAFE_JS
    assert "vex-positive" in MODERN_CSS
    assert "vex-negative" in MODERN_CSS
    assert "--vx-success" in MODERN_CSS
    assert "--vx-danger" in MODERN_CSS


def test_modern_layer_respects_reduced_motion_and_responsive_layouts():
    assert "prefers-reduced-motion" in MODERN_CSS
    assert "@media (max-width:900px)" in MODERN_CSS
    assert "@media (max-width:620px)" in MODERN_CSS
