from __future__ import annotations

import pytest
from fastapi.routing import APIRoute

import app.main as main_module
from app import login_enumeration_safety as safety


class _LoginRequest:
    def __init__(self, email: str, password: str = "test-password"):
        self.email = email
        self.password = password


def test_missing_login_user_spends_dummy_password_work(monkeypatch):
    work: list[str] = []
    calls: list[str] = []
    monkeypatch.setattr(safety, "_spend_dummy_password_work", lambda: work.append("pbkdf2"))

    def original(*, request):
        calls.append(str(request.email))
        return {"ok": False}

    guarded = safety._wrap_login_endpoint(original, lambda _email: None)
    request = _LoginRequest("missing@example.com")

    assert guarded(request=request) == {"ok": False}
    assert work == ["pbkdf2"]
    assert calls == ["missing@example.com"]


def test_current_known_login_user_leaves_real_password_work_to_original(monkeypatch):
    user = {
        "id": 7,
        "email": "known@example.com",
        "password_salt": "pbkdf2_sha256$600000$00112233445566778899aabbccddeeff",
        "password_hash": "00" * 32,
    }
    work: list[str] = []
    upgrades: list[int] = []
    monkeypatch.setattr(safety, "_spend_dummy_password_work", lambda: work.append("pbkdf2"))
    monkeypatch.setattr(safety, "_upgrade_legacy_password_record", lambda u, _p: upgrades.append(int(u["id"])))

    guarded = safety._wrap_login_endpoint(lambda **_kwargs: {"ok": True}, lambda _email: user)

    assert guarded(request=_LoginRequest("known@example.com")) == {"ok": True}
    assert work == []
    assert upgrades == []


def test_successful_legacy_login_is_rehashed_after_original_returns(monkeypatch):
    user = {
        "id": 8,
        "email": "legacy@example.com",
        "password_salt": "00112233445566778899aabbccddeeff",
        "password_hash": "11" * 32,
    }
    events: list[str] = []

    def original(*, request):
        events.append(f"authenticated:{request.email}")
        return {"ok": True}

    def upgrade(found_user, password):
        events.append(f"rehash:{found_user['id']}:{password}")

    monkeypatch.setattr(safety, "_upgrade_legacy_password_record", upgrade)
    guarded = safety._wrap_login_endpoint(original, lambda _email: user)

    result = guarded(request=_LoginRequest("legacy@example.com", "correct-password"))

    assert result == {"ok": True}
    assert events == [
        "authenticated:legacy@example.com",
        "rehash:8:correct-password",
    ]


def test_failed_legacy_login_never_rehashes(monkeypatch):
    user = {
        "id": 9,
        "email": "legacy@example.com",
        "password_salt": "00112233445566778899aabbccddeeff",
        "password_hash": "22" * 32,
    }
    upgrades: list[int] = []
    monkeypatch.setattr(safety, "_upgrade_legacy_password_record", lambda u, _p: upgrades.append(int(u["id"])))

    def rejected(**_kwargs):
        raise RuntimeError("invalid login")

    guarded = safety._wrap_login_endpoint(rejected, lambda _email: user)

    with pytest.raises(RuntimeError, match="invalid login"):
        guarded(request=_LoginRequest("legacy@example.com", "wrong-password"))
    assert upgrades == []


def test_legacy_rehash_uses_compare_and_set_without_session_revocation(tmp_path, monkeypatch):
    from app import store

    monkeypatch.setattr(store, "DB_PATH", tmp_path / "legacy-rehash.db")
    store.init_db()
    user_id, _ = store.create_user(
        "legacy-cas@example.com",
        "00112233445566778899aabbccddeeff",
        "33" * 32,
        "Legacy CAS",
    )
    user = store.get_user_by_email("legacy-cas@example.com")
    assert user is not None

    # A pre-existing session must survive an opportunistic KDF upgrade.
    store.create_session(user_id, "aa" * 32, "2099-01-01T00:00:00+00:00")
    safety._upgrade_legacy_password_record(user, "correct-password")

    upgraded = store.get_user_by_email("legacy-cas@example.com")
    assert upgraded is not None
    assert str(upgraded["password_salt"]).startswith("pbkdf2_sha256$600000$")
    with store._connect() as con:
        assert con.execute("SELECT COUNT(*) FROM sessions WHERE user_id=?", (user_id,)).fetchone()[0] == 1

    # Replaying the stale pre-upgrade row cannot overwrite a newer credential.
    current_salt = str(upgraded["password_salt"])
    safety._upgrade_legacy_password_record(user, "different-password")
    assert str(store.get_user_by_email("legacy-cas@example.com")["password_salt"]) == current_salt


def test_installer_is_scoped_to_login_route_only():
    routes = {
        route.path: route
        for route in main_module.app.routes
        if isinstance(route, APIRoute)
    }

    login_call = routes["/api/auth/login"].dependant.call
    reset_call = routes["/api/auth/password-reset/request"].dependant.call

    assert getattr(login_call, safety._GUARD_MARKER, False) is True
    assert getattr(reset_call, safety._GUARD_MARKER, False) is False


def test_installer_is_idempotent():
    login_route = next(
        route
        for route in main_module.app.routes
        if isinstance(route, APIRoute) and route.path == "/api/auth/login"
    )
    installed = login_route.dependant.call

    safety.install_login_enumeration_safety()

    assert login_route.dependant.call is installed
