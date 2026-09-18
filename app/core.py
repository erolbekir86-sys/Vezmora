from __future__ import annotations

from typing import Any

from .store import (
    campaign_summary,
    dashboard_summary,
    get_autopilot_settings,
    get_connectors,
    get_onboarding_profile,
    list_anomalies,
    list_approvals,
    recent_competitor_changes,
)


def core_today(workspace_id: int) -> dict[str, Any]:
    summary = dashboard_summary(workspace_id)
    anomalies = list_anomalies(workspace_id, 10)
    approvals = list_approvals(workspace_id, "pending", 20)
    changes = recent_competitor_changes(workspace_id, 10)
    campaigns = campaign_summary(workspace_id, 30)[:20]
    connectors = {c["provider"]: c for c in get_connectors(workspace_id)}
    onboarding = get_onboarding_profile(workspace_id)
    autopilot = get_autopilot_settings(workspace_id)

    cards: list[dict[str, Any]] = []
    for anomaly in anomalies[:3]:
        cards.append({
            "priority": "high" if anomaly.get("severity") == "high" else "medium",
            "source": "performance",
            "title": anomaly.get("title") or "Performance signal",
            "body": anomaly.get("body") or "",
            "cta": "Open Insights",
            "view": "insights",
        })
    if approvals:
        cards.append({
            "priority": "high",
            "source": "queue",
            "title": f"{len(approvals)} action(s) need a decision",
            "body": "Review pending actions before they block campaign progress.",
            "cta": "Review Queue",
            "view": "queue",
        })
    if changes:
        cards.append({
            "priority": "medium",
            "source": "rivals",
            "title": f"{len(changes)} competitor change(s) detected",
            "body": str(changes[0].get("name") or changes[0].get("title") or "A watched competitor changed"),
            "cta": "Open Rivals",
            "view": "rivals",
        })
    supported_live_sources = ("google", "meta", "instagram", "shopify")
    connected_live_sources = [
        provider
        for provider in supported_live_sources
        if connectors.get(provider) and connectors[provider].get("status") == "connected"
    ]
    if not connected_live_sources:
        cards.append({
            "priority": "medium",
            "source": "data",
            "title": "Connect live marketing data",
            "body": "Connect at least one supported source so Vexmera can work from real performance or commerce data instead of demo context.",
            "cta": "Connect data",
            "view": "connect",
        })
    if not onboarding.get("completed"):
        cards.append({
            "priority": "high",
            "source": "setup",
            "title": "Finish your growth onboarding",
            "body": "Complete the commercial brief so Core can prioritize against your real goal and budget.",
            "cta": "Finish setup",
            "view": "onboarding",
        })
    if not cards:
        cards.append({
            "priority": "low",
            "source": "core",
            "title": "No critical blockers detected",
            "body": "Core has no high-priority signal from the saved data. Run a sync or ask Core for the next growth experiment.",
            "cta": "Ask Core",
            "view": "agent",
        })

    cards = cards[:5]
    next_move = cards[0]
    return {
        "headline": next_move["title"],
        "summary": summary,
        "cards": cards,
        "autopilot": autopilot,
        "campaigns": campaigns[:5],
        "onboarding_complete": bool(onboarding.get("completed")),
    }
