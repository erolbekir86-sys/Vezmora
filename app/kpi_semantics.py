from __future__ import annotations

from typing import Any, Callable

from . import store as _store

_GOOGLE_ANALYTICS_SOURCE = "google_analytics"
_SHOPIFY_ORDERS_SOURCE = "shopify_orders"


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

        # Ad platforms can each report attributed conversion value for the same
        # sale. Once Shopify is connected, use actual store order totals as the
        # canonical workspace revenue/order count so the dashboard never sums
        # overlapping Google/Meta attribution with commerce revenue.
        shopify_rows = [
            row for row in raw_rows
            if str(row.get("source") or "") == _SHOPIFY_ORDERS_SOURCE
        ]
        if shopify_rows:
            revenue = sum(float(row.get("revenue_sek") or 0) for row in shopify_rows)
            orders = sum(int(row.get("conversions") or 0) for row in shopify_rows)
            spend = float(summary.get("spend_sek") or 0)
            summary["revenue_sek"] = revenue
            summary["conversions"] = orders
            summary["roas"] = (revenue / spend) if spend else 0
            summary["revenue_source"] = _SHOPIFY_ORDERS_SOURCE
            summary["conversions_source"] = _SHOPIFY_ORDERS_SOURCE
            summary["revenue_scope"] = "actual_store_revenue_not_summed_with_ad_attribution"
        else:
            summary["revenue_source"] = "provider_attribution_and_manual"
            summary["conversions_source"] = "provider_attribution_and_manual"
        return summary

    _store.list_kpis = list_kpis
    _store.dashboard_summary = dashboard_summary
    _store._vexmera_kpi_semantics_installed = True
