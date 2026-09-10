from __future__ import annotations

import json

from app.pricing import CURRENT_PRICING_VERSION, EXPECTED_MONTHLY_SEK_ORE
from scripts import stripe_sandbox_preflight as preflight


class FakePrices:
    def __init__(self, prices: dict[str, object], failures: dict[str, Exception] | None = None):
        self.prices = prices
        self.failures = failures or {}
        self.retrieved: list[str] = []

    def retrieve(self, price_id: str):
        self.retrieved.append(price_id)
        if price_id in self.failures:
            raise self.failures[price_id]
        return self.prices[price_id]


class FakeV1:
    def __init__(self, prices: FakePrices):
        self.prices = prices


class FakeClient:
    def __init__(self, prices: dict[str, object], failures: dict[str, Exception] | None = None):
        self.v1 = FakeV1(FakePrices(prices, failures))


def _set_valid_env(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_private_value")
    monkeypatch.setenv("STRIPE_PRICE_START", "price_start_private")
    monkeypatch.setenv("STRIPE_PRICE_GROWTH", "price_growth_private")
    monkeypatch.setenv("STRIPE_PRICE_PRO", "price_pro_private")
    monkeypatch.setenv("VEZMORA_STRIPE_PRICING_VERSION", CURRENT_PRICING_VERSION)


def _price(price_id: str, amount: int, **overrides):
    value = {
        "id": price_id,
        "active": True,
        "livemode": False,
        "currency": "sek",
        "type": "recurring",
        "unit_amount": amount,
        "recurring": {"interval": "month", "interval_count": 1},
    }
    value.update(overrides)
    return value


def _valid_client():
    return FakeClient(
        {
            "price_start_private": _price("price_start_private", EXPECTED_MONTHLY_SEK_ORE["start"]),
            "price_growth_private": _price("price_growth_private", EXPECTED_MONTHLY_SEK_ORE["growth"]),
            "price_pro_private": _price("price_pro_private", EXPECTED_MONTHLY_SEK_ORE["pro"]),
        }
    )


def test_valid_sandbox_catalog_and_marker_pass(monkeypatch):
    _set_valid_env(monkeypatch)
    client = _valid_client()

    result = preflight.build_stripe_sandbox_preflight(client)

    assert result["ok"] is True
    assert result["catalog_ok"] is True
    assert result["pricing_version_marker_matches"] is True
    assert result["blockers"] == []
    assert all(plan["ok"] is True for plan in result["plans"].values())
    assert client.v1.prices.retrieved == [
        "price_start_private",
        "price_growth_private",
        "price_pro_private",
    ]


def test_valid_catalog_does_not_open_gate_without_exact_marker(monkeypatch):
    _set_valid_env(monkeypatch)
    monkeypatch.delenv("VEZMORA_STRIPE_PRICING_VERSION", raising=False)

    result = preflight.build_stripe_sandbox_preflight(_valid_client())

    assert result["catalog_ok"] is True
    assert result["pricing_version_marker_matches"] is False
    assert result["ok"] is False
    assert result["blockers"] == ["pricing_version_marker_not_approved"]


def test_live_mode_or_wrong_amount_is_rejected(monkeypatch):
    _set_valid_env(monkeypatch)
    client = _valid_client()
    client.v1.prices.prices["price_growth_private"] = _price(
        "price_growth_private",
        999_999,
        livemode=True,
    )

    result = preflight.build_stripe_sandbox_preflight(client)

    assert result["catalog_ok"] is False
    assert result["ok"] is False
    assert "growth_sandbox" in result["blockers"]
    assert "growth_expected_amount" in result["blockers"]


def test_non_monthly_inactive_or_wrong_currency_is_rejected(monkeypatch):
    _set_valid_env(monkeypatch)
    client = _valid_client()
    client.v1.prices.prices["price_pro_private"] = _price(
        "price_pro_private",
        EXPECTED_MONTHLY_SEK_ORE["pro"],
        active=False,
        currency="eur",
        recurring={"interval": "year", "interval_count": 1},
    )

    result = preflight.build_stripe_sandbox_preflight(client)

    assert "pro_active" in result["blockers"]
    assert "pro_currency_sek" in result["blockers"]
    assert "pro_monthly_interval" in result["blockers"]
    assert result["plans"]["pro"]["ok"] is False


def test_malformed_numeric_fields_become_mismatches_not_crashes(monkeypatch):
    _set_valid_env(monkeypatch)
    client = _valid_client()
    client.v1.prices.prices["price_start_private"] = _price(
        "price_start_private",
        EXPECTED_MONTHLY_SEK_ORE["start"],
        unit_amount="not-a-number",
        recurring={"interval": "month", "interval_count": "invalid"},
    )

    result = preflight.build_stripe_sandbox_preflight(client)

    assert "start_interval_count_one" in result["blockers"]
    assert "start_expected_amount" in result["blockers"]
    assert "start_price_lookup_failed" not in result["blockers"]


def test_lookup_failure_is_safe_and_does_not_surface_raw_stripe_error(monkeypatch):
    _set_valid_env(monkeypatch)
    client = _valid_client()
    client.v1.prices.failures["price_start_private"] = RuntimeError(
        "Stripe request failed with sk_test_private_value and price_start_private"
    )

    result = preflight.build_stripe_sandbox_preflight(client)
    serialized = json.dumps(result)

    assert "start_price_lookup_failed" in result["blockers"]
    assert "sk_test_private_value" not in serialized
    assert "price_start_private" not in serialized
    assert "Stripe request failed" not in serialized


def test_report_never_emits_secret_key_or_configured_price_ids(monkeypatch):
    _set_valid_env(monkeypatch)

    result = preflight.build_stripe_sandbox_preflight(_valid_client())
    serialized = json.dumps(result)

    assert "sk_test_private_value" not in serialized
    assert "price_start_private" not in serialized
    assert "price_growth_private" not in serialized
    assert "price_pro_private" not in serialized


def test_missing_configuration_fails_closed_without_network_client(monkeypatch):
    for name in (
        "STRIPE_SECRET_KEY",
        "STRIPE_PRICE_START",
        "STRIPE_PRICE_GROWTH",
        "STRIPE_PRICE_PRO",
        "VEZMORA_STRIPE_PRICING_VERSION",
    ):
        monkeypatch.delenv(name, raising=False)

    result = preflight.build_stripe_sandbox_preflight()

    assert result["ok"] is False
    assert result["catalog_ok"] is False
    assert "stripe_secret_key_missing" in result["blockers"]
    assert "start_price_id_missing" in result["blockers"]
    assert "growth_price_id_missing" in result["blockers"]
    assert "pro_price_id_missing" in result["blockers"]


def test_preflight_source_contains_only_price_retrieve_for_stripe_actions():
    source = open(preflight.__file__, encoding="utf-8").read()

    assert ".v1.prices.retrieve(" in source
    for forbidden in (
        ".create(",
        ".update(",
        ".delete(",
        "checkout.sessions.create",
        "subscriptions.create",
        "products.create",
        "prices.create",
        "os.environ[",
    ):
        assert forbidden not in source
