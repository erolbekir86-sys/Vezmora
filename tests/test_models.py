from app.models import CompanyProfile, StrategyRequest


def test_strategy_request_defaults():
    company = CompanyProfile(
        name="Test Co",
        industry="Retail",
        audience="Adults in Sweden",
        offer="Useful products",
    )
    req = StrategyRequest(company=company)
    assert req.objective == "sales"
    assert req.horizon_days == 30
    assert req.company.language == "sv"
