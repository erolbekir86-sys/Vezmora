from datetime import datetime, timedelta, timezone
from pathlib import Path

import app.main as app_main
import app.store as store
import app.workspace_billing_defaults as defaults


ROOT = Path(__file__).resolve().parents[1]
INIT = (ROOT / "app" / "__init__.py").read_text(encoding="utf-8")
STORE = (ROOT / "app" / "store.py").read_text(encoding="utf-8")


def test_new_user_workspace_gets_start_plan_and_bounded_trial(monkeypatch):
    calls = []
    monkeypatch.setattr(defaults, "_ORIGINAL_CREATE_USER", lambda *args: (10, 20))
    monkeypatch.setattr(store, "set_workspace_billing", lambda workspace_id, **kwargs: calls.append((workspace_id, kwargs)))

    before = datetime.now(timezone.utc)
    result = defaults.create_user_with_current_workspace_defaults("a@example.com", "salt", "hash", "Pilot")
    after = datetime.now(timezone.utc)

    assert result == (10, 20)
    assert len(calls) == 1
    workspace_id, kwargs = calls[0]
    assert workspace_id == 20
    assert kwargs["plan"] == "start"
    assert kwargs["billing_status"] == "trialing"
    trial_end = datetime.fromisoformat(kwargs["trial_ends_at"])
    assert before + timedelta(days=14) <= trial_end <= after + timedelta(days=14)


def test_new_extra_workspace_gets_same_current_defaults(monkeypatch):
    calls = []
    monkeypatch.setattr(defaults, "_ORIGINAL_CREATE_WORKSPACE", lambda user_id, name: 77)
    monkeypatch.setattr(store, "set_workspace_billing", lambda workspace_id, **kwargs: calls.append((workspace_id, kwargs)))

    workspace_id = defaults.create_workspace_with_current_defaults(5, "Extra")

    assert workspace_id == 77
    assert calls[0][0] == 77
    assert calls[0][1]["plan"] == "start"
    assert calls[0][1]["billing_status"] == "trialing"
    assert calls[0][1]["trial_ends_at"] is not None


def test_current_defaults_are_bound_before_main_imports_create_functions():
    assert INIT.index("install_workspace_billing_defaults") < INIT.index("from .main import app as _app")
    assert app_main.create_user is store.create_user
    assert app_main.create_workspace is store.create_workspace
    assert store.create_user is defaults.create_user_with_current_workspace_defaults
    assert store.create_workspace is defaults.create_workspace_with_current_defaults


def test_patch_is_forward_only_and_keeps_legacy_reader_compatibility():
    source = Path(defaults.__file__).read_text(encoding="utf-8")
    assert "CURRENT_DEFAULT_PLAN = \"start\"" in source
    assert "DEFAULT_TRIAL_DAYS = 14" in source
    assert "Historical workspace rows are deliberately left untouched" in source
    assert "UPDATE workspace_settings" not in source
    # The old schema default may remain for compatibility, but new creation is
    # explicitly initialized by the early wrapper instead of relying on it.
    assert "plan TEXT NOT NULL DEFAULT 'starter'" in STORE


def test_workspace_default_patch_does_not_touch_stripe_or_external_systems():
    source = Path(defaults.__file__).read_text(encoding="utf-8")
    for forbidden in (
        "StripeClient",
        "STRIPE_SECRET_KEY",
        "STRIPE_PRICE_",
        "httpx",
        "requests",
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "META_APP_SECRET",
        "campaign",
        "budget",
    ):
        assert forbidden not in source
