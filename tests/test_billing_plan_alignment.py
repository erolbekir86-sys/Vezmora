from __future__ import annotations

from app.pricing import EXPECTED_MONTHLY_SEK_ORE, PLANS, normalize_plan


def test_customer_facing_plan_prices_and_team_limits_match_public_model():
    assert PLANS["start"]["monthly_price_sek"] == 995
    assert PLANS["start"]["team_members"] == 1

    assert PLANS["growth"]["monthly_price_sek"] == 1495
    assert PLANS["growth"]["team_members"] == 3

    assert PLANS["pro"]["monthly_price_sek"] == 2995
    assert PLANS["pro"]["team_members"] == 10

    assert EXPECTED_MONTHLY_SEK_ORE == {
        "start": 99_500,
        "growth": 149_500,
        "pro": 299_500,
    }


def test_plan_capacity_increases_monotonically():
    names = ("start", "growth", "pro")
    for key in ("ai_runs", "jobs", "team_members", "campaign_rows", "monthly_price_sek"):
        values = [int(PLANS[name][key]) for name in names]
        assert values == sorted(values)
        assert len(set(values)) == len(values)


def test_historical_plan_names_normalize_without_data_migration():
    assert normalize_plan("starter") == "start"
    assert normalize_plan("scale") == "pro"
    assert normalize_plan("growth") == "growth"
