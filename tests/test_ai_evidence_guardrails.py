from pathlib import Path


def test_base_ai_instructions_require_evidence_labels():
    source = Path("app/agent.py").read_text(encoding="utf-8")

    assert "Observed data" in source
    assert "User-provided context" in source
    assert "Assumption" in source
    assert "Never invent performance data" in source
    assert "Do not present an Assumption" in source


def test_strategy_and_brief_keep_missing_data_distinct_from_observed_performance():
    source = Path("app/agent.py").read_text(encoding="utf-8")

    assert "If no connected KPI/competitor evidence supports a claim" in source
    assert "Never convert a missing-data assumption into a performance claim" in source
    assert "REQUIRES APPROVAL" in source
