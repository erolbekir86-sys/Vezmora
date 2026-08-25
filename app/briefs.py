from __future__ import annotations

from typing import Any

from .store import create_approval, dashboard_summary, list_approvals, recent_competitor_changes, campaign_summary, list_anomalies


def brief_memory(workspace_id: int) -> dict[str, Any]:
    return {
        "kpi_summary": dashboard_summary(workspace_id),
        "recent_competitor_changes": recent_competitor_changes(workspace_id, 10),
        "campaign_performance_30d": campaign_summary(workspace_id, 30)[:20],
        "recent_anomalies": list_anomalies(workspace_id, 10),
        "pending_approvals": list_approvals(workspace_id, "pending", 20),
    }


def create_metric_proposals(workspace_id: int, created_by: int | None = None) -> list[int]:
    """Create conservative, review-only proposals from deterministic KPI signals."""
    summary = dashboard_summary(workspace_id)
    created: list[int] = []
    if summary.get("spend_sek", 0) > 0 and summary.get("roas", 0) < 1.5:
        created.append(create_approval(
            workspace_id, created_by, "budget_review", "Review paid-media allocation",
            f"Current aggregated ROAS is {summary.get('roas', 0):.2f}x. Review channel-level spend before increasing budget.",
            "paid_media", "high", {"current_roas": summary.get("roas", 0), "suggested_execution": "analysis_only"},
        ))
    if summary.get("impressions", 0) >= 1000 and summary.get("ctr", 0) < 1.0:
        created.append(create_approval(
            workspace_id, created_by, "creative_refresh", "Prepare a creative refresh",
            f"Aggregated CTR is {summary.get('ctr', 0):.2f}%. Prepare new hooks/creative variants for review before publishing.",
            "paid_media", "medium", {"current_ctr": summary.get("ctr", 0), "suggested_execution": "draft_only"},
        ))
    return created
