from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models import CompanyProfile, OnboardingProfile


def _company(**overrides):
    values = {
        "name": "Acme AB",
        "industry": "Software",
        "audience": "Swedish SMEs",
        "offer": "Marketing intelligence",
    }
    values.update(overrides)
    return CompanyProfile(**values)


def _onboarding(**overrides):
    values = {
        "company_name": "Acme AB",
        "industry": "Software",
        "audience": "Swedish SMEs",
        "offer": "Marketing intelligence",
    }
    values.update(overrides)
    return OnboardingProfile(**values)


def test_required_company_context_trims_surrounding_whitespace() -> None:
    company = _company(industry="  Software  ", audience="  Swedish SMEs  ", offer="  Marketing intelligence  ")
    onboarding = _onboarding(industry="  Services  ", audience="  Local businesses  ", offer="  Consulting  ")

    assert company.industry == "Software"
    assert company.audience == "Swedish SMEs"
    assert company.offer == "Marketing intelligence"
    assert onboarding.industry == "Services"
    assert onboarding.audience == "Local businesses"
    assert onboarding.offer == "Consulting"


@pytest.mark.parametrize("field", ["industry", "audience", "offer"])
def test_company_profile_rejects_whitespace_only_required_context(field: str) -> None:
    with pytest.raises(ValidationError):
        _company(**{field: "    "})


@pytest.mark.parametrize("field", ["industry", "audience", "offer"])
def test_onboarding_rejects_whitespace_only_required_context(field: str) -> None:
    with pytest.raises(ValidationError):
        _onboarding(**{field: "    "})
