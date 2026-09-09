from __future__ import annotations

from app import store


def test_google_analytics_sessions_are_not_counted_as_paid_clicks(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "kpi-semantics.db")
    store.init_db()
    _, workspace_id = store.create_user("semantics@example.com", "salt", "hash", "Semantics test")

    store.add_kpi(
        workspace_id,
        {
            "date": "2026-09-08",
            "impressions": 0,
            "clicks": 120,  # historical beta storage shape: this is GA sessions
            "leads": 0,
            "conversions": 3,
            "spend_sek": 0,
            "revenue_sek": 500,
            "source": "google_analytics",
            "currency": "SEK",
        },
    )
    store.add_kpi(
        workspace_id,
        {
            "date": "2026-09-08",
            "impressions": 100,
            "clicks": 10,
            "leads": 2,
            "conversions": 1,
            "spend_sek": 200,
            "revenue_sek": 400,
            "source": "google_ads",
            "currency": "SEK",
        },
    )

    rows = store.list_kpis(workspace_id, 20)
    ga = next(row for row in rows if row["source"] == "google_analytics")
    ads = next(row for row in rows if row["source"] == "google_ads")

    assert ga["sessions"] == 120
    assert ga["clicks"] == 0
    assert ga["metric_semantics"] == "website_sessions"
    assert ads["clicks"] == 10
    assert ads["sessions"] == 0

    summary = store.dashboard_summary(workspace_id)
    assert summary["sessions"] == 120
    assert summary["clicks"] == 10
    assert summary["ctr"] == 10.0
    assert summary["cpc"] == 20.0
    assert summary["clicks_scope"] == "paid_media_and_manual_excluding_google_analytics_sessions"
    assert summary["sessions_source"] == "google_analytics"
