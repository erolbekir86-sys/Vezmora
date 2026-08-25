from app.postgres_compat import _sql


def test_sqlite_compat_translation():
    assert _sql("BEGIN IMMEDIATE") == "BEGIN"
    assert "INTERVAL '20 minutes'" in _sql(
        "SELECT * FROM oauth_states WHERE created_at >= datetime('now','-20 minutes')"
    )
    assert "ON CONFLICT DO NOTHING" in _sql(
        "INSERT OR IGNORE INTO workspace_settings(workspace_id) VALUES(?)"
    )
    assert "ON CONFLICT(workspace_id,user_id) DO UPDATE SET role=EXCLUDED.role" in _sql(
        "INSERT OR REPLACE INTO workspace_members(workspace_id,user_id,role) VALUES(?,?,?)"
    )
    assert "CAST(%s AS interval)" in _sql(
        "SELECT * FROM campaign_metrics WHERE metric_date>=date('now', ?)"
    )
