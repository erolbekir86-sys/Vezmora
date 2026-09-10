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


def test_relative_datetime_translation_supports_bounded_units_generically():
    cases = {
        "datetime('now','-10 minutes')": "CURRENT_TIMESTAMP - INTERVAL '10 minutes'",
        "datetime('now','+45 minutes')": "CURRENT_TIMESTAMP + INTERVAL '45 minutes'",
        "datetime('now','-2 hours')": "CURRENT_TIMESTAMP - INTERVAL '2 hours'",
        "datetime('now','+1 day')": "CURRENT_TIMESTAMP + INTERVAL '1 day'",
        "datetime('now','-7 days')": "CURRENT_TIMESTAMP - INTERVAL '7 days'",
    }
    for sqlite_expr, postgres_expr in cases.items():
        translated = _sql(f"SELECT * FROM events WHERE created_at >= {sqlite_expr}")
        assert postgres_expr in translated
        assert "datetime('now'" not in translated


def test_relative_datetime_translation_does_not_rewrite_unapproved_units_or_start_anchors():
    unsupported = "datetime('now','-2 months')"
    translated = _sql(f"SELECT {unsupported}, datetime('now','start of day'), datetime('now','start of month')")

    assert unsupported in translated
    assert "date_trunc('day', CURRENT_TIMESTAMP)" in translated
    assert "date_trunc('month', CURRENT_TIMESTAMP)" in translated


def test_relative_datetime_translation_preserves_parameter_conversion():
    translated = _sql(
        "SELECT * FROM events WHERE created_at >= datetime('now','-30 minutes') AND workspace_id=?"
    )
    assert "CURRENT_TIMESTAMP - INTERVAL '30 minutes'" in translated
    assert translated.count("%s") == 1
