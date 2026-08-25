from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field, HttpUrl

Language = Literal["sv", "en", "de", "es", "fr", "tr"]
Objective = Literal["awareness", "leads", "sales", "bookings", "retention", "launch"]
ApprovalStatus = Literal["pending", "approved", "rejected", "executed", "failed"]
WorkspaceRole = Literal["owner", "admin", "marketer", "viewer"]


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)
    workspace_name: str = Field(default="My Workspace", min_length=2, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class CompanyProfile(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    industry: str = Field(min_length=2, max_length=120)
    market: str = Field(default="Sweden", max_length=120)
    website: HttpUrl | None = None
    audience: str = Field(min_length=3, max_length=800)
    offer: str = Field(min_length=3, max_length=800)
    brand_voice: str = Field(default="clear, trustworthy, useful", max_length=500)
    language: Language = "sv"


class StrategyRequest(BaseModel):
    company: CompanyProfile | None = None
    objective: Objective = "sales"
    budget_sek: int | None = Field(default=None, ge=0, le=10_000_000)
    horizon_days: int = Field(default=30, ge=7, le=365)
    notes: str = Field(default="", max_length=1500)


class CampaignRequest(BaseModel):
    company: CompanyProfile | None = None
    objective: Objective = "sales"
    channel: Literal["meta", "google", "tiktok", "linkedin", "email", "organic"] = "meta"
    campaign_name: str = Field(default="New campaign", max_length=120)
    budget_sek: int | None = Field(default=None, ge=0, le=10_000_000)
    notes: str = Field(default="", max_length=1500)


class AgentRequest(BaseModel):
    company: CompanyProfile | None = None
    message: str = Field(min_length=2, max_length=5000)


class AgentResponse(BaseModel):
    output: str
    model: str


class KPIEntry(BaseModel):
    date: date
    currency: str = Field(default="SEK", min_length=3, max_length=3)
    impressions: int = Field(default=0, ge=0)
    clicks: int = Field(default=0, ge=0)
    leads: int = Field(default=0, ge=0)
    conversions: int = Field(default=0, ge=0)
    spend_sek: float = Field(default=0, ge=0)
    revenue_sek: float = Field(default=0, ge=0)
    source: str = Field(default="manual", max_length=80)


class CompetitorCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    url: HttpUrl | None = None
    notes: str = Field(default="", max_length=1500)


class ConnectorSettings(BaseModel):
    analytics_property_id: str | None = Field(default=None, max_length=80)
    ads_customer_id: str | None = Field(default=None, max_length=80)
    meta_ad_account_id: str | None = Field(default=None, max_length=100)


class SyncRequest(BaseModel):
    days: int = Field(default=7, ge=1, le=90)


class DailyBriefSettings(BaseModel):
    enabled: bool = False
    hour: int = Field(default=8, ge=0, le=23)
    timezone: str = Field(default="Europe/Stockholm", min_length=3, max_length=80)


class ApprovalCreate(BaseModel):
    action_type: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=3, max_length=180)
    description: str = Field(min_length=3, max_length=4000)
    provider: str | None = Field(default=None, max_length=60)
    risk_level: Literal["low", "medium", "high"] = "medium"
    payload: dict[str, Any] = Field(default_factory=dict)


class ApprovalDecision(BaseModel):
    note: str = Field(default="", max_length=1500)


class WorkspaceSettings(BaseModel):
    base_currency: str = Field(default="SEK", min_length=3, max_length=3)


class FXRateUpsert(BaseModel):
    quote_currency: str = Field(min_length=3, max_length=3)
    rate_to_base: float = Field(gt=0, le=1_000_000)


class TeamInviteRequest(BaseModel):
    email: EmailStr
    role: Literal["admin", "marketer", "viewer"] = "marketer"


class TeamJoinRequest(BaseModel):
    token: str = Field(min_length=20, max_length=300)


class ApprovalExecuteRequest(BaseModel):
    confirm: bool = False


class JobCreateRequest(BaseModel):
    kind: Literal["sync_all", "sync_google", "sync_meta", "scan_rivals", "detect_anomalies", "daily_brief", "autopilot_tick", "initial_strategy"]
    payload: dict[str, Any] = Field(default_factory=dict)


class BillingPlanUpdate(BaseModel):
    plan: Literal["starter", "growth", "scale"]

AutopilotMode = Literal["suggest", "assisted", "autopilot"]


class OnboardingProfile(BaseModel):
    company_name: str = Field(min_length=2, max_length=120)
    industry: str = Field(min_length=2, max_length=120)
    market: str = Field(default="Sweden", max_length=120)
    website: HttpUrl | None = None
    audience: str = Field(min_length=3, max_length=800)
    offer: str = Field(min_length=3, max_length=800)
    brand_voice: str = Field(default="clear, trustworthy, useful", max_length=500)
    language: Language = "sv"
    primary_goal: Objective = "sales"
    monthly_budget: float = Field(default=0, ge=0, le=100_000_000)
    primary_channels: list[Literal["meta", "google", "tiktok", "linkedin", "email", "organic"]] = Field(default_factory=list, max_length=6)
    growth_target: str = Field(default="", max_length=500)
    biggest_marketing_problem: str = Field(default="", max_length=1000)
    timezone: str = Field(default="Europe/Stockholm", min_length=3, max_length=80)
    team_size: int = Field(default=1, ge=1, le=100_000)


class AutopilotSettings(BaseModel):
    mode: AutopilotMode = "suggest"
    daily_spend_cap: float = Field(default=0, ge=0, le=100_000_000)
    max_budget_change_pct: float = Field(default=15, ge=0, le=100)
    allowed_actions: list[Literal[
        "google.pause_campaign",
        "google.enable_campaign",
        "google.set_daily_budget",
        "meta.pause_campaign",
        "meta.activate_campaign",
    ]] = Field(default_factory=list)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=20, max_length=300)
    password: str = Field(min_length=8, max_length=200)


class BetaFeedbackCreate(BaseModel):
    score: int = Field(ge=1, le=5)
    category: Literal["general", "core", "data", "campaigns", "billing", "bug"] = "general"
    message: str = Field(default="", max_length=4000)


class BillingCheckoutRequest(BaseModel):
    plan: Literal["starter", "growth", "scale"]


class CoreActionCreate(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    rationale: str = Field(min_length=3, max_length=2000)
    action_type: str = Field(min_length=2, max_length=80)
    provider: str | None = Field(default=None, max_length=60)
    risk_level: Literal["low", "medium", "high"] = "medium"
    payload: dict[str, Any] = Field(default_factory=dict)
