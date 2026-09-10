from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _text(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_production_runbook_keeps_public_runtime_minimal() -> None:
    text = _text("PRODUCTION_ENVIRONMENT.md")
    section = text.split("## Safe runtime diagnostics", 1)[1].split("## Privacy controls", 1)[0]

    assert "intentionally minimal" in section
    assert "scripts/preflight.py" in section
    for forbidden in (
        "`database_connection_ok`",
        "`openai_connection_ok`",
        "`internal_secrets_configured`",
        "`stripe_configured`",
        "`smtp_configured`",
        "`google_oauth_configured`",
        "`meta_oauth_configured`",
    ):
        assert forbidden not in section


def test_meta_runbook_does_not_depend_on_public_oauth_configuration_flags() -> None:
    text = _text("META_OAUTH_SETUP.md")

    assert "/health/runtime` returns `meta_oauth_configured: true`" not in text
    assert "bounded Insights pagination" in text
    assert "bounded retry" in text
    assert "provider/API failure" in text
    assert "scripts/preflight.py" in text


def test_launch_plan_does_not_freeze_a_static_main_sha_as_release_truth() -> None:
    text = _text("LAUNCH_GAP_PLAN.md")

    assert "Latest verified `main` commit:" not in text
    assert "Do not use a hard-coded commit SHA" in text
    assert "verify the current `main` SHA" in text
