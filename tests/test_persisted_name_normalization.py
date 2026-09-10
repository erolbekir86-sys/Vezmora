from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models import CompanyProfile, CompetitorCreate, OnboardingProfile, RegisterRequest, WorkspaceCreate


def test_persisted_identity_names_trim_surrounding_whitespace() -> None:
    register = RegisterRequest(email="owner@example.com", password="password123", workspace_name="  North Star  ")
    workspace = WorkspaceCreate(name="  Growth Lab  ")
    company = CompanyProfile(
        name="  Acme AB  ",
        industry="Software",
        audience="Swedish SMEs",
        offer="Marketing intelligence",
    )
    onboarding = OnboardingProfile(
        company_name="  Pilot AB  ",
        industry="Services",
        audience="Local businesses",
        offer="Consulting services",
    )
    competitor = CompetitorCreate(name="  Rival AB  ")

    assert register.workspace_name == "North Star"
    assert workspace.name == "Growth Lab"
    assert company.name == "Acme AB"
    assert onboarding.company_name == "Pilot AB"
    assert competitor.name == "Rival AB"


@pytest.mark.parametrize(
    "factory",
    [
        lambda: RegisterRequest(email="owner@example.com", password="password123", workspace_name="   "),
        lambda: WorkspaceCreate(name="   "),
        lambda: CompanyProfile(name="   ", industry="Software", audience="Swedish SMEs", offer="Marketing intelligence"),
        lambda: OnboardingProfile(company_name="   ", industry="Services", audience="Local businesses", offer="Consulting services"),
        lambda: CompetitorCreate(name="   "),
    ],
)
def test_persisted_identity_names_reject_whitespace_only(factory) -> None:
    with pytest.raises(ValidationError):
        factory()


def test_password_and_capability_fields_are_not_normalized_by_name_guard() -> None:
    password = "  password123  "
    request = RegisterRequest(email="owner@example.com", password=password, workspace_name="Workspace")
    assert request.password == password
