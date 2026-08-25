from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from .store import add_notification, list_kpis, save_anomaly


def _window(rows: list[dict[str, Any]], start: date, end: date) -> dict[str, float]:
    out = defaultdict(float)
    for row in rows:
        try:
            d = date.fromisoformat(str(row["metric_date"]))
        except ValueError:
            continue
        if start <= d <= end:
            for key in ("impressions", "clicks", "leads", "conversions", "spend_sek", "revenue_sek"):
                out[key] += float(row.get(key, 0) or 0)
    out["ctr"] = 100 * out["clicks"] / out["impressions"] if out["impressions"] else 0
    out["roas"] = out["revenue_sek"] / out["spend_sek"] if out["spend_sek"] else 0
    out["cpl"] = out["spend_sek"] / out["leads"] if out["leads"] else 0
    return dict(out)


def _pct(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return (current - previous) / previous


def detect_anomalies(workspace_id: int, anchor: date | None = None) -> list[dict[str, Any]]:
    anchor = anchor or date.today()
    rows = list_kpis(workspace_id, 400)
    current = _window(rows, anchor - timedelta(days=6), anchor)
    previous = _window(rows, anchor - timedelta(days=13), anchor - timedelta(days=7))
    findings: list[dict[str, Any]] = []

    rules = [
        ("roas_drop", _pct(current["roas"], previous["roas"]), -0.25, "high", "ROAS dropped", "Return on ad spend is down by more than 25% versus the previous 7-day window."),
        ("ctr_drop", _pct(current["ctr"], previous["ctr"]), -0.25, "medium", "CTR dropped", "Click-through rate is down by more than 25% versus the previous 7-day window."),
        ("spend_spike", _pct(current["spend_sek"], previous["spend_sek"]), 0.35, "medium", "Spend increased", "Spend is up by more than 35% versus the previous 7-day window."),
        ("conversion_drop", _pct(current["conversions"], previous["conversions"]), -0.30, "high", "Conversions dropped", "Conversions are down by more than 30% versus the previous 7-day window."),
    ]
    for code, delta, threshold, severity, title, body in rules:
        if delta is None:
            continue
        triggered = delta <= threshold if threshold < 0 else delta >= threshold
        if not triggered:
            continue
        metadata = {"code": code, "delta": round(delta, 4), "current": current, "previous": previous, "anchor": anchor.isoformat()}
        fingerprint = hashlib.sha256(json.dumps({"code": code, "anchor": anchor.isoformat()}, sort_keys=True).encode()).hexdigest()
        created = save_anomaly(workspace_id, fingerprint, severity, title, body, metadata)
        finding = {"fingerprint": fingerprint, "severity": severity, "title": title, "body": body, "metadata": metadata, "new": created}
        findings.append(finding)
        if created:
            add_notification(workspace_id, "anomaly", title, body, metadata)
    return findings
