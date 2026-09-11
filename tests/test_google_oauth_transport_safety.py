from pathlib import Path

from app import connectors
from app import main as app_main
from app.google_oauth_transport_safety import google_callback_safe


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "app" / "google_oauth_transport_safety.py").read_text(encoding="utf-8")
INIT_SOURCE = (ROOT / "app" / "__init__.py").read_text(encoding="utf-8")


def test_google_callback_is_bound_to_safe_transport_before_app_route_import() -> None:
    assert connectors.google_callback is google_callback_safe
    assert app_main.google_callback is google_callback_safe
    assert INIT_SOURCE.index("install_google_oauth_transport_safety") < INIT_SOURCE.index(
        "from . import connector_privacy_controls"
    )


def test_google_oauth_exchange_uses_fixed_endpoint_and_no_redirects() -> None:
    assert "AsyncClient(timeout=20, follow_redirects=False)" in SOURCE
    assert "client.post(_connectors.GOOGLE_TOKEN_URL" in SOURCE
    assert "Google token exchange returned an invalid response" in SOURCE
    assert "access_token" in SOURCE


def test_google_oauth_transport_guard_does_not_change_scopes_or_execution() -> None:
    forbidden = (
        "GOOGLE_SCOPES =",
        "ads_management",
        "VEZMORA_EXECUTION_ENABLED",
        "VEZMORA_AUTOPILOT_EXECUTION_ENABLED",
        "pause_campaign",
        "daily_budget",
    )
    for marker in forbidden:
        assert marker not in SOURCE
