from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models import FXRateUpsert, KPIEntry, WorkspaceSettings


def test_currency_models_accept_three_letter_codes_case_insensitively() -> None:
    assert WorkspaceSettings(base_currency="sek").base_currency == "sek"
    assert FXRateUpsert(quote_currency="usd", rate_to_base=1).quote_currency == "usd"
    assert KPIEntry(date="2026-09-10", currency="eur").currency == "eur"


@pytest.mark.parametrize(
    "factory",
    [
        lambda: WorkspaceSettings(base_currency="12!"),
        lambda: FXRateUpsert(quote_currency="U$D", rate_to_base=1),
        lambda: KPIEntry(date="2026-09-10", currency="1SE"),
        lambda: WorkspaceSettings(base_currency="SE"),
        lambda: WorkspaceSettings(base_currency="SEKK"),
    ],
)
def test_currency_models_reject_non_three_letter_codes(factory) -> None:
    with pytest.raises(ValidationError):
        factory()
