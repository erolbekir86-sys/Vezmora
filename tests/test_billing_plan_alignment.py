from __future__ import annotations

from app.billing import PLANS


def test_customer_facing_plan_prices_and_team_limits_are_aligned():
    assert PLANS["starter"]["monthly_price_sek"] == 1499
    assert PLANS["starter"]["team_members"] == 1

    assert PLANS["growth"]["monthly_price_sek"] == 2999
    assert PLANS["growth"]["team_members"] == 3

    assert PLANS["scale"]["monthly_price_sek"] == 5999
    assert PLANS["scale"]["team_members"] == 10


def test_plan_capacity_increases_monotonically():
    names = ("starter", "growth", "scale")
    for key in ("ai_runs", "jobs", "team_members", "campaign_rows", "monthly_price_sek"):
        values = [int(PLANS[name][key]) for name in names]
        assert values == sorted(values)
        assert len(set(values)) == len(values)
