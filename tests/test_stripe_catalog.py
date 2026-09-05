from __future__ import annotations

from types import SimpleNamespace

from app import stripe_catalog


def _price(amount: int, *, currency: str = "sek", active: bool = True, interval: str = "month"):
    return {
        "object": "price",
        "active": active,
        "currency": currency,
        "unit_amount": amount,
        "recurring": {"interval": interval, "interval_count": 1},
    }


def test_validate_expected_vexmera_monthly_prices():
    for plan, amount in stripe_catalog.EXPECTED_MONTHLY_SEK_ORE.items():
        assert stripe_catalog.validate_price_payload(plan, _price(amount)) == (True, "ok")


def test_validate_rejects_wrong_amount_currency_or_interval():
    assert stripe_catalog.validate_price_payload("starter", _price(99_900))[1] == "amount_mismatch"
    assert stripe_catalog.validate_price_payload("starter", _price(149_900, currency="usd"))[1] == "currency_mismatch"
    assert stripe_catalog.validate_price_payload("starter", _price(149_900, interval="year"))[1] == "interval_mismatch"


def test_verify_configured_prices_returns_safe_status(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_placeholder")
    monkeypatch.setenv("STRIPE_PRICE_STARTER", "price_starter")
    monkeypatch.setenv("STRIPE_PRICE_GROWTH", "price_growth")
    monkeypatch.setenv("STRIPE_PRICE_SCALE", "price_scale")

    payloads = {
        "price_starter": _price(149_900),
        "price_growth": _price(299_900),
        "price_scale": _price(599_900),
    }

    def fake_get(url, **kwargs):
        price_id = url.rsplit("/", 1)[-1]
        return SimpleNamespace(status_code=200, json=lambda: payloads[price_id])

    monkeypatch.setattr(stripe_catalog.httpx, "get", fake_get)
    result = stripe_catalog.verify_configured_prices()
    assert result["ok"] is True
    assert result["configured"] is True
    assert set(result["plans"]) == {"starter", "growth", "scale"}
    serialized = repr(result)
    assert "sk_test_placeholder" not in serialized
    assert "price_starter" not in serialized
