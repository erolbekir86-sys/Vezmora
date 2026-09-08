from __future__ import annotations

from scripts import pilot_go_no_go


def _configuration(ok: bool = True) -> dict[str, object]:
    return {
        "ok": ok,
        "manual_verification_required": True,
        "manual_gates": ["authenticated_browser_qa"],
    }


def test_go_no_go_without_base_url_is_configuration_only(monkeypatch):
    monkeypatch.setattr(pilot_go_no_go, "build_preflight_snapshot", lambda: _configuration(True))

    result = pilot_go_no_go.build_go_no_go_snapshot()

    assert result["ok"] is True
    assert result["status"] == "machine_checks_clear"
    assert result["pilot_ready"] is None
    assert result["manual_verification_required"] is True
    assert "live" not in result
    assert "legal_discoverability" not in result
    assert "does not approve" in result["note"]


def test_go_no_go_combines_live_and_legal_checks(monkeypatch):
    monkeypatch.setattr(pilot_go_no_go, "build_preflight_snapshot", lambda: _configuration(True))
    monkeypatch.setattr(
        pilot_go_no_go,
        "build_live_preflight",
        lambda base_url: {"ok": True, "base_url": base_url, "blockers": []},
    )
    monkeypatch.setattr(
        pilot_go_no_go,
        "build_public_legal_preflight",
        lambda base_url: {"ok": True, "base_url": base_url, "blockers": []},
    )

    result = pilot_go_no_go.build_go_no_go_snapshot("https://vexmera.com")

    assert result["ok"] is True
    assert result["live"]["ok"] is True
    assert result["legal_discoverability"]["ok"] is True


def test_go_no_go_fails_closed_when_legal_discoverability_fails(monkeypatch):
    monkeypatch.setattr(pilot_go_no_go, "build_preflight_snapshot", lambda: _configuration(True))
    monkeypatch.setattr(
        pilot_go_no_go,
        "build_live_preflight",
        lambda base_url: {"ok": True, "base_url": base_url, "blockers": []},
    )
    monkeypatch.setattr(
        pilot_go_no_go,
        "build_public_legal_preflight",
        lambda base_url: {
            "ok": False,
            "base_url": base_url,
            "blockers": ["privacy_not_linked_from_homepage"],
        },
    )

    result = pilot_go_no_go.build_go_no_go_snapshot("https://vexmera.com")

    assert result["ok"] is False
    assert result["status"] == "blocked"
    assert result["legal_discoverability"]["blockers"] == ["privacy_not_linked_from_homepage"]


def test_go_no_go_preserves_configuration_blocker(monkeypatch):
    monkeypatch.setattr(pilot_go_no_go, "build_preflight_snapshot", lambda: _configuration(False))
    monkeypatch.setattr(pilot_go_no_go, "build_live_preflight", lambda base_url: {"ok": True})
    monkeypatch.setattr(pilot_go_no_go, "build_public_legal_preflight", lambda base_url: {"ok": True})

    result = pilot_go_no_go.build_go_no_go_snapshot("https://vexmera.com")

    assert result["ok"] is False
    assert result["status"] == "blocked"
