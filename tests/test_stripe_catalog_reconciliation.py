from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.pricing import (
    CURRENT_PRICING_VERSION,
    CURRENT_TEST_PRICE_IDS,
    STRIPE_PRICE_ENV,
    current_stripe_catalog_reconciled,
    current_stripe_price_ids_match,
)


def _set_verified_catalog(monkeypatch) -> None:
    monkeypatch.setenv("VEZMORA_STRIPE_PRICING_VERSION", CURRENT_PRICING_VERSION)
    for plan, price_id in CURRENT_TEST_PRICE_IDS.items():
        monkeypatch.setenv(STRIPE_PRICE_ENV[plan], price_id)


def test_verified_stripe_catalog_reports_reconciled(monkeypatch) -> None:
    _set_verified_catalog(monkeypatch)

    assert current_stripe_price_ids_match() is True
    assert current_stripe_catalog_reconciled() is True

    with TestClient(app) as client:
        payload = client.get("/health").json()

    assert payload["stripe_current_prices_configured"] is True
    assert payload["stripe_pricing_version_current"] is True
    assert payload["stripe_price_ids_current"] is True
    assert payload["stripe_catalog_reconciled"] is True


def test_wrong_stripe_price_fails_closed(monkeypatch) -> None:
    _set_verified_catalog(monkeypatch)
    monkeypatch.setenv("STRIPE_PRICE_PRO", "price_wrong_pro")

    assert current_stripe_price_ids_match() is False
    assert current_stripe_catalog_reconciled() is False

    with TestClient(app) as client:
        payload = client.get("/health").json()

    assert payload["stripe_current_prices_configured"] is True
    assert payload["stripe_pricing_version_current"] is True
    assert payload["stripe_price_ids_current"] is False
    assert payload["stripe_catalog_reconciled"] is False


def test_stale_pricing_version_fails_closed(monkeypatch) -> None:
    _set_verified_catalog(monkeypatch)
    monkeypatch.setenv("VEZMORA_STRIPE_PRICING_VERSION", "legacy-starter-growth-scale")

    assert current_stripe_price_ids_match() is True
    assert current_stripe_catalog_reconciled() is False

    with TestClient(app) as client:
        payload = client.get("/health").json()

    assert payload["stripe_current_prices_configured"] is True
    assert payload["stripe_pricing_version_current"] is False
    assert payload["stripe_price_ids_current"] is True
    assert payload["stripe_catalog_reconciled"] is False
