from __future__ import annotations

import json
import os
from typing import Any

from .models import AgentRequest, CampaignRequest, StrategyRequest

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-terra")

LANGUAGE_NAMES = {
    "sv": "Swedish",
    "en": "English",
    "de": "German",
    "es": "Spanish",
    "fr": "French",
    "tr": "Turkish",
}

BASE_INSTRUCTIONS = """
You are Vexmera, an AI Chief Marketing Officer for small and growing businesses.
You do not behave like a generic copywriter. You think like a commercially accountable marketing leader.

Core behavior:
- Start from the company's commercial objective, audience, offer and market.
- Prefer specific actions over vague advice.
- Separate assumptions from facts supplied by the user.
- Never invent performance data, competitors, market statistics or customer evidence.
- When data is missing, state the assumption and propose the fastest way to validate it.
- For non-trivial recommendations, make the evidence basis explicit as one of: Observed data, User-provided context, or Assumption.
- Do not present an Assumption as if it came from connected analytics, ad-platform data, competitor monitoring or customer evidence.
- Recommend experiments with a hypothesis, action, KPI and decision rule.
- Use saved KPI and competitor context when supplied.
- Keep brand voice and local market context in mind.
- For anything that would spend money, publish content, message customers or change an ad account, propose the action but require human approval.
- Return clean Markdown suitable for rendering in a dashboard.
"""


def _load_agents():
    try:
        from agents import Agent, Runner, function_tool
    except ImportError as exc:
        raise RuntimeError("openai-agents is not installed. Run: uv sync") from exc
    return Agent, Runner, function_tool


def _company_context(company: Any) -> str:
    data = company.model_dump(mode="json")
    return "COMPANY PROFILE\n" + json.dumps(data, ensure_ascii=False, indent=2)


def _business_memory(memory: dict[str, Any] | None) -> str:
    if not memory:
        return "BUSINESS MEMORY\nNo saved KPI or competitor context available yet."
    return "BUSINESS MEMORY\n" + json.dumps(memory, ensure_ascii=False, indent=2)


def _agent(language: str):
    Agent, _, function_tool = _load_agents()

    @function_tool
    def funnel_framework(objective: str) -> str:
        """Return a deterministic marketing funnel framework for a business objective."""
        frameworks = {
            "awareness": ["Reach", "Video views", "Engaged audience", "Retargeting"],
            "leads": ["Problem-aware content", "Lead magnet", "Lead capture", "Follow-up"],
            "sales": ["Demand", "Product proof", "Conversion", "Retargeting", "Retention"],
            "bookings": ["Local discovery", "Trust proof", "Booking CTA", "No-show prevention"],
            "retention": ["Activation", "Value reminder", "Win-back", "Referral"],
            "launch": ["Tease", "Reveal", "Launch", "Proof", "Retargeting"],
        }
        return json.dumps(frameworks.get(objective, frameworks["sales"]))

    @function_tool
    def channel_playbook(channel: str) -> str:
        """Return practical constraints and strengths for a marketing channel."""
        playbooks = {
            "meta": "Strong for visual demand generation, retargeting and local audiences. Lead with a hook, proof and one clear CTA.",
            "google": "Strong for existing intent. Group keywords tightly, match landing page intent and separate brand from non-brand.",
            "tiktok": "Strong for native short-form creative. Prioritize creator-style hooks, fast pacing and multiple creative variants.",
            "linkedin": "Strong for B2B and professional audiences. Use specific business pain, quantified value and credible proof.",
            "email": "Strong for owned-audience conversion and retention. Segment, personalize and keep one primary action per message.",
            "organic": "Strong for trust and compounding reach. Build repeatable content pillars and convert attention into an owned audience.",
        }
        return playbooks.get(channel, playbooks["organic"])

    language_name = LANGUAGE_NAMES.get(language, "English")
    return Agent(
        name="Vexmera CMO",
        model=MODEL,
        instructions=BASE_INSTRUCTIONS + f"\nAlways write the final answer in {language_name}, unless the user explicitly requests another language.",
        tools=[funnel_framework, channel_playbook],
    )


async def generate_strategy(request: StrategyRequest, memory: dict[str, Any] | None = None) -> str:
    if request.company is None:
        raise ValueError("Company profile is required")
    _, Runner, _ = _load_agents()
    prompt = f"""
{_company_context(request.company)}

{_business_memory(memory)}

TASK
Create a practical {request.horizon_days}-day marketing strategy.
Primary objective: {request.objective}
Budget in SEK: {request.budget_sek if request.budget_sek is not None else 'not specified'}
Additional notes: {request.notes or 'none'}

Use the funnel framework. Include:
1. Executive diagnosis
2. Positioning/message angle
3. Channel priorities with rationale
4. Weekly action plan
5. 3-5 experiments, each with hypothesis, KPI and decision rule
6. Budget allocation if a budget exists
7. What Vexmera should measure next
8. Human approvals required before execution

Evidence discipline:
- For each major recommendation, label its basis as Observed data, User-provided context, or Assumption.
- If no connected KPI/competitor evidence supports a claim, do not word it as an observed performance fact.
"""
    result = await Runner.run(_agent(request.company.language), prompt)
    return str(result.final_output)


async def generate_campaign(request: CampaignRequest, memory: dict[str, Any] | None = None) -> str:
    if request.company is None:
        raise ValueError("Company profile is required")
    _, Runner, _ = _load_agents()
    prompt = f"""
{_company_context(request.company)}

{_business_memory(memory)}

TASK
Build a campaign package.
Campaign: {request.campaign_name}
Objective: {request.objective}
Channel: {request.channel}
Budget in SEK: {request.budget_sek if request.budget_sek is not None else 'not specified'}
Additional notes: {request.notes or 'none'}

Produce:
- Campaign thesis
- Audience and intent
- Offer/CTA
- 5 hooks
- 3 ad/copy variants
- Creative directions
- Landing-page outline
- KPI plan
- 2 A/B tests
- Launch checklist
- Explicit approval gate before anything is published or money is spent

Evidence discipline:
- Separate known company/customer facts from targeting or creative assumptions.
- Label material assumptions that should be validated before launch.
"""
    result = await Runner.run(_agent(request.company.language), prompt)
    return str(result.final_output)


async def run_agent(request: AgentRequest, memory: dict[str, Any] | None = None) -> str:
    if request.company is None:
        raise ValueError("Company profile is required")
    _, Runner, _ = _load_agents()
    prompt = f"""
{_company_context(request.company)}

{_business_memory(memory)}

USER REQUEST
{request.message}

Act as the company's strategic marketing operator. Distinguish observed data and user-provided facts from assumptions in recommendations. If the request implies publishing, spending, contacting people or modifying an external account, prepare the action but stop at an approval gate.
"""
    result = await Runner.run(_agent(request.company.language), prompt)
    return str(result.final_output)


async def generate_daily_brief(company: Any, memory: dict[str, Any] | None = None) -> str:
    """Generate an executive morning brief from persisted workspace signals."""
    _, Runner, _ = _load_agents()
    prompt = f"""
{_company_context(company)}

{_business_memory(memory)}

TASK
Create a concise executive marketing morning brief. Use only the supplied data.

Include:
1. What changed
2. Performance pulse: strongest and weakest signal
3. Competitor changes worth attention
4. The three highest-value actions for today
5. Experiments to continue, stop, or inspect
6. Pending approvals that block progress
7. Data gaps or connector issues

For each recommended action, make clear whether it is supported by Observed data, User-provided context, or an Assumption. Never convert a missing-data assumption into a performance claim.
For any recommendation that would spend money, publish content, contact customers, or mutate an external account, explicitly label it as REQUIRES APPROVAL.
Do not claim that an action has been executed.
"""
    result = await Runner.run(_agent(getattr(company, "language", "en")), prompt)
    return str(result.final_output)
