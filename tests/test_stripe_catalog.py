from __future__ import annotations

import json

from stripe import StripeClient

from app import stripe_catalog
from app.pricing import CURRENT_PRICING_VERSION


class FakePrices:
    def __init__(self, payloads: dict[str, object], failures: dict[str, Exception] | None = None):
        self.payloads = payloads
        self.failures = failures or {}
        self.retrieved: list[str] = []

    def retrieve(self, price_id: str):
        self.retrieved.append(price_id)
        if price_id in self.failures:
            raise self.failures[price_id]
        return self.payloads[price_id]


class FakeClient:
    def __init__(self, payloads: dict[str, object], failures: dict[str, Exception] | None = None):
        self.v1 = type("V1", (), {"prices": FakePrices(payloads, failures)})()


def _price(
    amount: int,
    *,
    price_id: str = "price_test",
    currency: str = "sek",
    active: bool = True,
    livemode: bool = False,
    interval: str = "month",
    interval_count: object = 1,
    price_type: str = "recurring",
    unit_amount: object | None = None,
):
    return {
        "id": price_id,
        "object": "price",
        "active": active,
        "livemode": livemode,
        "currency": currency,
        "type": price_type,
        "unit_amount": amount if unit_amount is None else unit_amount,
        "recurring": {"interval": interval, "interval_count": interval_count},
    }


def _set_valid_env(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_private_value")
    monkeypatch.setenv("STRIPE_PRICE_START", "price_start_private")
    monkeypatch.setenv("STRIPE_PRICE_GROWTH", "price_growth_private")
    monkeypatch.setenv("STRIPE_PRICE_PRO", "price_pro_private")
    monkeypatch.setenv("VEZMORA_STRIPE_PRICING_VERSION", CURRENT_PRICING_VERSION)


def _valid_client():
    return FakeClient(
        {
            "price_start_private": _price(99_500, price_id="price_start_private"),
            "price_growth_private": _price(149_500, price_id="price_growth_private"),
            "price_pro_private": _price(299_500, price_id="price_pro_private"),
        }
    )


def test_installed_stripe_sdk_exposes_v1_price_retrieve_without_network_call():
    client = StripeClient("sk_test_offline_contract_check", max_network_retries=0)

    assert callable(client.v1.prices.retrieve)


def test_validate_expected_vexmera_monthly_sandbox_prices():
    for plan, amount in stripe_catalog.EXPECTED_MONTHLY_SEK_ORE.items():
        assert stripe_catalog.validate_price_payload(plan, _price(amount)) == (True, "ok")


def test_validate_rejects_live_mode_wrong_amount_currency_interval_and_type():
    assert stripe_catalog.validate_price_payload("start", _price(99_500, livemode=True))[1] == "livemode_not_sandbox"
    assert stripe_catalog.validate_price_payload("start", _price(99_900))[1] == "amount_mismatch"
    assert stripe_catalog.validate_price_payload("start", _price(99_500, currency="usd"))[1] == "currency_mismatch"
    assert stripe_catalog.validate_price_payload("start", _price(99_500, interval="year"))[1] == "interval_mismatch"
    assert stripe_catalog.validate_price_payload("start", _price(99_500, price_type="one_time"))[1] == "not_recurring"


def test_validate_rejects_configured_price_id_mismatch():
    payload = _price(99_500, price_id="price_other")

    assert stripe_catalog.validate_price_payload("start", payload, "price_configured") == (
        False,
        "price_id_mismatch",
    )


def test_malformed_numeric_fields_become_validation_failures_not_crashes():
    payload = _price(
        99_500,
        unit_amount="not-a-number",
        interval_count="invalid",
    )
    checks = stripe_catalog.price_validation_checks("start", payload)

    assert checks["interval_count_one"] is False
    assert checks["expected_amount"] is False


def test_verify_configured_prices_accepts_only_exact_current_sandbox_catalog(monkeypatch):
    _set_valid_env(monkeypatch)
    client = _valid_client()

    result = stripe_catalog.verify_configured_prices(client)

    assert result["ok"] is True
    assert result["catalog_ok"] is True
    assert result["configured"] is True
    assert result["pricing_version_marker_matches"] is True
    assert result["blockers"] == []
    assert set(result["plans"]) == {"start", "growth", "pro"}
    assert client.v1.prices.retrieved == [
        "price_start_private",
        "price_growth_private",
        "price_pro_private",
    ]


def test_valid_catalog_does_not_open_gate_without_exact_pricing_marker(monkeypatch):
    _set_valid_env(monkeypatch)
    monkeypatch.delenv("VEZMORA_STRIPE_PRICING_VERSION", raising=False)

    result = stripe_catalog.verify_configured_prices(_valid_client())

    assert result["catalog_ok"] is True
    assert result["pricing_version_marker_matches"] is False
    assert result["ok"] is False
    assert result["blockers"] == ["pricing_version_marker_not_approved"]


def test_verify_rejects_live_mode_and_wrong_amount(monkeypatch):
    _set_valid_env(monkeypatch)
    client = _valid_client()
    client.v1.prices.payloads["price_growth_private"] = _price(
        999_999,
        price_id="price_growth_private",
        livemode=True,
    )

    result = stripe_catalog.verify_configured_prices(client)

    assert result["catalog_ok"] is False
    assert "growth_sandbox" in result["blockers"]
    assert "growth_expected_amount" in result["blockers"]


def test_lookup_failure_is_safe_and_does_not_surface_raw_stripe_error(monkeypatch):
    _set_valid_env(monkeypatch)
    client = _valid_client()
    client.v1.prices.failures["price_start_private"] = RuntimeError(
        "Stripe failed with sk_test_private_value and price_start_private"
    )

    result = stripe_catalog.verify_configured_prices(client)
    serialized = json.dumps(result)

    assert "start_price_lookup_failed" in result["blockers"]
    assert "sk_test_private_value" not in serialized
    assert "price_start_private" not in serialized
    assert "Stripe failed" not in serialized


def test_report_never_emits_secret_key_or_configured_price_ids(monkeypatch):
    _set_valid_env(monkeypatch)

    result = stripe_catalog.verify_configured_prices(_valid_client())
    serialized = json.dumps(result)

    assert "sk_test_private_value" not in serialized
    assert "price_start_private" not in serialized
    assert "price_growth_private" not in serialized
    assert "price_pro_private" not in serialized


def test_missing_configuration_fails_closed_without_client(monkeypatch):
    for name in (
        "STRIPE_SECRET_KEY",
        "STRIPE_PRICE_START",
        "STRIPE_PRICE_GROWTH",
        "STRIPE_PRICE_PRO",
        "VEZMORA_STRIPE_PRICING_VERSION",
    ):
        monkeypatch.delenv(name, raising=False)

    result = stripe_catalog.verify_configured_prices()

    assert result["ok"] is False
    assert result["catalog_ok"] is False
    assert "stripe_secret_key_missing" in result["blockers"]
    assert "start_price_id_missing" in result["blockers"]
    assert "growth_price_id_missing" in result["blockers"]
    assert "pro_price_id_missing" in result["blockers"]


def test_canonical_verifier_contains_only_price_retrieve_for_stripe_actions():
    source = open(stripe_catalog.__file__, encoding="utf-8").read()

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
