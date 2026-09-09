from __future__ import annotations

from typing import Any, Callable

from . import store as _store

_GOOGLE_ANALYTICS_SOURCE = "google_analytics"


def _semantic_row(row: dict[str, Any]) -> dict[str, Any]:
    item = dict(row)
    if str(item.get("source") or "") == _GOOGLE_ANALYTICS_SOURCE:
        # Historical beta rows store GA sessions in the generic `clicks` column.
        # Do not rewrite production history in-place. Translate that legacy shape
        # at the read boundary so every consumer sees website sessions as sessions
        # and never as paid-media clicks.
        item["sessions"] = int(item.get("clicks") or 0)
        item["clicks"] = 0
        item["metric_semantics"] = "website_sessions"
    else:
        item["sessions"] = int(item.get("sessions") or 0)
        item["metric_semantics"] = "paid_or_manual_kpi"
    return item


def install_kpi_semantics_guard() -> None:
    if getattr(_store, "_vexmera_kpi_semantics_installed", False):
        return

    original_list_kpis: Callable[..., list[dict[str, Any]]] = _store.list_kpis
    original_dashboard_summary = _store.dashboard_summary

    def list_kpis(workspace_id: int, limit: int = 90) -> list[dict[str, Any]]:
        return [_semantic_row(row) for row in original_list_kpis(workspace_id, limit)]

    def dashboard_summary(workspace_id: int) -> dict[str, Any]:
        # The original summary resolves store.list_kpis at call time. Installing
        # the semantic list wrapper first makes CTR/CPC paid-click-safe without
        # duplicating the mature summary calculations.
        summary = dict(original_dashboard_summary(workspace_id))
        raw_rows = original_list_kpis(workspace_id, 3650)
        sessions = sum(
            int(row.get("clicks") or 0)
            for row in raw_rows
            if str(row.get("source") or "") == _GOOGLE_ANALYTICS_SOURCE
        )
        summary["sessions"] = sessions
        summary["clicks_scope"] = "paid_media_and_manual_excluding_google_analytics_sessions"
        summary["sessions_source"] = "google_analytics"
        return summary

    _store.list_kpis = list_kpis
    _store.dashboard_summary = dashboard_summary
    _store._vexmera_kpi_semantics_installed = True
