from __future__ import annotations

from fastapi.testclient import TestClient

from app import account_privacy_controls, connectors, store
from app.auth import hash_password
from app.main import app


PASSWORD = "verysecure123"


def _register(client: TestClient, email: str = "delete-test@example.com") -> int:
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": PASSWORD,
            "workspace_name": "Deletion Test",
        },
    )
    assert response.status_code == 200
    return response.json()["workspace_id"]


def test_account_deletion_preview_allows_solo_owner_without_subscription(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "account-preview.db")
    store.init_db()

    with TestClient(app) as client:
        workspace_id = _register(client)
        response = client.get("/api/privacy/account-deletion-preview")
        assert response.status_code == 200
        payload = response.json()
        assert payload["allowed"] is True
        assert payload["confirmation_phrase"] == "DELETE MY ACCOUNT"
        assert payload["requires_password_reauthentication"] is True
        assert payload["shared_workspace_memberships"] == 0
        assert payload["owned_workspaces"] == [
            {
                "id": workspace_id,
                "name": "Deletion Test",
                "member_count": 1,
                "billing_status": "trialing",
                "subscription_attached": False,
                "active_subscription": False,
            }
        ]
        assert payload["blockers"] == []


def test_account_deletion_requires_current_password(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "account-password.db")
    store.init_db()

    with TestClient(app) as client:
        _register(client)
        response = client.request(
            "DELETE",
            "/api/privacy/account",
            json={"password": "wrong-password", "confirmation": "DELETE MY ACCOUNT"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Current password is incorrect"
        assert client.get("/api/auth/me").status_code == 200


def test_account_deletion_blocks_owned_workspace_with_other_members(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "account-members.db")
    store.init_db()

    with TestClient(app) as client:
        workspace_id = _register(client)
        salt, password_hash = hash_password("second-user-password")
        second_user_id, _ = store.create_user(
            "second-user@example.com",
            salt,
            password_hash,
            "Second workspace",
        )
        store.add_workspace_member(workspace_id, second_user_id, "viewer")

        preview = client.get("/api/privacy/account-deletion-preview").json()
        assert preview["allowed"] is False
        assert preview["owned_workspaces"][0]["member_count"] == 2
        assert preview["blockers"][0]["code"] == "workspace_has_other_members"

        response = client.request(
            "DELETE",
            "/api/privacy/account",
            json={"password": PASSWORD, "confirmation": "DELETE MY ACCOUNT"},
        )
        assert response.status_code == 409
        assert "Transfer ownership" in response.json()["detail"]
        assert client.get("/api/auth/me").status_code == 200


def test_account_deletion_blocks_attached_active_subscription(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "account-billing.db")
    store.init_db()

    with TestClient(app) as client:
        workspace_id = _register(client)
        store.set_workspace_billing(
            workspace_id,
            customer_id="cus_test",
            subscription_id="sub_test",
            billing_status="active",
        )

        preview = client.get("/api/privacy/account-deletion-preview").json()
        assert preview["allowed"] is False
        assert preview["owned_workspaces"][0]["active_subscription"] is True
        assert preview["blockers"][0]["code"] == "active_subscription"

        response = client.request(
            "DELETE",
            "/api/privacy/account",
            json={"password": PASSWORD, "confirmation": "DELETE MY ACCOUNT"},
        )
        assert response.status_code == 409
        assert "Cancel the active Stripe subscription" in response.json()["detail"]


def test_account_deletion_removes_local_account_data_and_attempts_oauth_revocation(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "account-delete.db")
    monkeypatch.setenv("VEZMORA_SECRET_KEY", "account-deletion-connector-secret")
    store.init_db()

    revoke_calls: list[tuple[str, str | None]] = []

    async def fake_revoke(provider: str, secret_blob: str | None):
        revoke_calls.append((provider, secret_blob))
        return True, provider == "google"

    monkeypatch.setattr(account_privacy_controls._connector_privacy, "_revoke_provider_token", fake_revoke)

    with TestClient(app) as client:
        workspace_id = _register(client)
        user = store.get_user_by_email("delete-test@example.com")
        assert user is not None
        user_id = int(user["id"])

        store.save_connector(
            workspace_id=workspace_id,
            provider="google",
            status="connected",
            external_id="google-account",
            account_label="Google account",
            secret_blob=connectors.encrypt_json({"access_token": "google-token"}),
            metadata={},
        )
        store.save_connector(
            workspace_id=workspace_id,
            provider="meta",
            status="connected",
            external_id="meta-account",
            account_label="Meta account",
            secret_blob=connectors.encrypt_json({"access_token": "meta-token"}),
            metadata={},
        )
        with store._connect() as con:
            con.execute(
                """INSERT INTO workspace_invites
                   (workspace_id, email, role, token_hash, invited_by, expires_at)
                   VALUES (?, ?, 'viewer', 'pending-invite-token', ?, '2099-01-01T00:00:00+00:00')""",
                (workspace_id, "delete-test@example.com", user_id),
            )
            con.execute(
                """INSERT INTO email_outbox(workspace_id, recipient, subject, body_text)
                   VALUES (NULL, ?, 'Reset', 'Example queued email')""",
                ("delete-test@example.com",),
            )

        response = client.request(
            "DELETE",
            "/api/privacy/account",
            json={"password": PASSWORD, "confirmation": "DELETE MY ACCOUNT"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["account_deleted"] is True
        assert payload["local_data_deleted"] == {
            "owned_workspaces": 1,
            "shared_memberships": 0,
            "pending_invites": 1,
            "queued_email": 1,
        }
        assert payload["provider_token_revocation"] == {"attempted": 2, "succeeded": 1}
        assert payload["third_party_billing_records_may_be_retained"] is True
        assert sorted(provider for provider, _ in revoke_calls) == ["google", "meta"]

        assert client.get("/api/auth/me").status_code == 401
        with store._connect() as con:
            assert con.execute("SELECT COUNT(*) FROM users WHERE id=?", (user_id,)).fetchone()[0] == 0
            assert con.execute("SELECT COUNT(*) FROM workspaces WHERE id=?", (workspace_id,)).fetchone()[0] == 0
            assert con.execute(
                "SELECT COUNT(*) FROM workspace_invites WHERE lower(email)=lower(?)",
                ("delete-test@example.com",),
            ).fetchone()[0] == 0
            assert con.execute(
                "SELECT COUNT(*) FROM email_outbox WHERE lower(recipient)=lower(?)",
                ("delete-test@example.com",),
            ).fetchone()[0] == 0


def test_account_deletion_removes_membership_but_preserves_other_users_workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "account-shared-membership.db")
    store.init_db()

    with TestClient(app) as client:
        owned_workspace_id = _register(client)
        deleting_user = store.get_user_by_email("delete-test@example.com")
        assert deleting_user is not None

        salt, password_hash = hash_password("other-owner-password")
        other_owner_id, shared_workspace_id = store.create_user(
            "other-owner@example.com",
            salt,
            password_hash,
            "Other owner workspace",
        )
        assert other_owner_id != int(deleting_user["id"])
        store.add_workspace_member(shared_workspace_id, int(deleting_user["id"]), "marketer")

        preview = client.get("/api/privacy/account-deletion-preview").json()
        assert preview["allowed"] is True
        assert preview["shared_workspace_memberships"] == 1

        response = client.request(
            "DELETE",
            "/api/privacy/account",
            json={"password": PASSWORD, "confirmation": "DELETE MY ACCOUNT"},
        )
        assert response.status_code == 200
        assert response.json()["local_data_deleted"]["owned_workspaces"] == 1
        assert response.json()["local_data_deleted"]["shared_memberships"] == 1

        with store._connect() as con:
            assert con.execute("SELECT COUNT(*) FROM workspaces WHERE id=?", (owned_workspace_id,)).fetchone()[0] == 0
            assert con.execute("SELECT COUNT(*) FROM workspaces WHERE id=?", (shared_workspace_id,)).fetchone()[0] == 1
            assert con.execute(
                "SELECT COUNT(*) FROM workspace_members WHERE workspace_id=? AND user_id=?",
                (shared_workspace_id, int(deleting_user["id"])),
            ).fetchone()[0] == 0
