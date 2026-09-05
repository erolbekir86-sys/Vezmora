from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models import SyncRequest


APP_JS = Path("static/app.js").read_text(encoding="utf-8")


def test_private_beta_ui_exposes_only_supported_sync_periods():
    """Keep the pilot UI contract explicit: 7, 30, or 90 days."""
    for days in (7, 30, 90):
        assert f'<option value="{days}"' in APP_JS

    assert "return [7,30,90].includes(value)?value:30;" in APP_JS


def test_backend_accepts_all_private_beta_sync_periods():
    for days in (7, 30, 90):
        assert SyncRequest(days=days).days == days


@pytest.mark.parametrize("days", [0, 91, -1, 365])
def test_backend_rejects_out_of_bounds_sync_periods(days):
    with pytest.raises(ValidationError):
        SyncRequest(days=days)
