from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import Depends, HTTPException, Response
from pydantic import BaseModel, Field

from . import connector_privacy_controls as _connector_privacy
from . import store as _store
from .auth import require_user, verify_password
from .main import app as _app

User = Annotated[dict[str, Any], Depends(require_user)]
_ACCOUNT_DELETE_CONFIRMATION = "DELETE MY ACCOUNT"
_INACTIVE_SUBSCRIPTION_STATES = {"canceled", "incomplete_expired"}


class AccountDeleteRequest(BaseModel):
    password: str = Field(min_length=1, max_length=200)
    confirmation: Literal["DELETE MY ACCOUNT"]


def _owned_workspace_rows(user_id: int) -> list[dict[str, Any]]:
    with _store._connect() as con:
        rows = con.execute(
            """SELECT w.id, w.name,
                      COALESCE(ws.billing_status, 'trialing') AS billing_status,
                      ws.stripe_subscription_id,
                      (SELECT COUNT(*) FROM workspace_members wm WHERE wm.workspace_id=w.id) AS member_count
               FROM workspaces w
               LEFT JOIN workspace_settings ws ON ws.workspace_id=w.id
               WHERE w.owner_user_id=?
               ORDER BY w.id""",
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def account_deletion_snapshot(user_id: int) -> dict[str, Any]:
    owned = _owned_workspace_rows(user_id)
    blockers: list[dict[str, Any]] = []
    safe_owned: list[dict[str, Any]] = []

    for workspace in owned:
        member_count = int(workspace.get("member_count") or 0)
        billing_status = str(workspace.get("billing_status") or "trialing")
        subscription_attached = bool(workspace.get("stripe_subscription_id"))
        active_subscription = subscription_attached and billing_status not in _INACTIVE_SUBSCRIPTION_STATES

        safe_workspace = {
            "id": int(workspace["id"]),
            "name": str(workspace["name"]),
            "member_count": member_count,
            "billing_status": billing_status,
            "subscription_attached": subscription_attached,
            "active_subscription": active_subscription,
        }
        safe_owned.append(safe_workspace)

        if member_count > 1:
            blockers.append(
                {
                    "code": "workspace_has_other_members",
                    "workspace_id": int(workspace["id"]),
                    "workspace_name": str(workspace["name"]),
                    "message": "Transfer ownership or remove the other workspace members before deleting this account.",
                }
            )
        if active_subscription:
            blockers.append(
                {
                    "code": "active_subscription",
                    "workspace_id": int(workspace["id"]),
                    "workspace_name": str(workspace["name"]),
                    "message": "Cancel the active Stripe subscription before deleting this account.",
                }
            )

    with _store._connect() as con:
        shared_memberships = int(
            con.execute(
                """SELECT COUNT(*)
                   FROM workspace_members wm
                   JOIN workspaces w ON w.id=wm.workspace_id
                   WHERE wm.user_id=? AND w.owner_user_id<>?""",
                (user_id, user_id),
            ).fetchone()[0]
        )

    return {
        "allowed": not blockers,
        "confirmation_phrase": _ACCOUNT_DELETE_CONFIRMATION,
        "requires_password_reauthentication": True,
        "owned_workspaces": safe_owned,
        "shared_workspace_memberships": shared_memberships,
        "blockers": blockers,
        "deletion_scope": {
            "account_credentials": True,
            "sessions": True,
            "solo_owned_workspaces": True,
            "owned_workspace_data": True,
            "membership_in_other_workspaces": True,
            "pending_invites_for_account_email": True,
            "queued_email_for_account_email": True,
            "third_party_billing_records": False,
        },
        "notes": [
            "Owned workspaces are deleted with the account only when no other members remain.",
            "Membership in workspaces owned by someone else is removed; shared business records remain with those workspaces and user references are detached where supported.",
            "OAuth token revocation is attempted for Google and Meta on solo-owned workspaces before local account data is deleted.",
            "Stripe or other processors may retain billing records when required for accounting, fraud prevention or legal obligations.",
        ],
    }


async def _revoke_owned_connector_tokens(owned_workspaces: list[dict[str, Any]]) -> dict[str, int]:
    attempted = 0
    succeeded = 0
    for workspace in owned_workspaces:
        workspace_id = int(workspace["id"])
        for provider in ("google", "meta"):
            connector = _store.get_connector(workspace_id, provider, include_secret=True)
            if not connector or not connector.get("secret_blob"):
                continue
            did_attempt, did_succeed = await _connector_privacy._revoke_provider_token(
                provider,
                connector.get("secret_blob"),
            )
            if did_attempt:
                attempted += 1
            if did_succeed:
                succeeded += 1
    return {"attempted": attempted, "succeeded": succeeded}


def _delete_local_account(user_id: int, email: str) -> dict[str, int]:
    snapshot = account_deletion_snapshot(user_id)
    if not snapshot["allowed"]:
        raise RuntimeError("Account deletion blockers changed before deletion")

    with _store._connect() as con:
        invite_count = int(
            con.execute(
                "SELECT COUNT(*) FROM workspace_invites WHERE lower(email)=lower(?)",
                (email,),
            ).fetchone()[0]
        )
        outbox_count = int(
            con.execute(
                "SELECT COUNT(*) FROM email_outbox WHERE lower(recipient)=lower(?)",
                (email,),
            ).fetchone()[0]
        )
        owned_workspace_count = int(
            con.execute("SELECT COUNT(*) FROM workspaces WHERE owner_user_id=?", (user_id,)).fetchone()[0]
        )
        shared_membership_count = int(
            con.execute(
                """SELECT COUNT(*) FROM workspace_members wm
                   JOIN workspaces w ON w.id=wm.workspace_id
                   WHERE wm.user_id=? AND w.owner_user_id<>?""",
                (user_id, user_id),
            ).fetchone()[0]
        )

        con.execute("DELETE FROM workspace_invites WHERE lower(email)=lower(?)", (email,))
        con.execute("DELETE FROM email_outbox WHERE lower(recipient)=lower(?)", (email,))
        con.execute("DELETE FROM users WHERE id=?", (user_id,))

    return {
        "owned_workspaces": owned_workspace_count,
        "shared_memberships": shared_membership_count,
        "pending_invites": invite_count,
        "queued_email": outbox_count,
    }


@_app.get("/api/privacy/account-deletion-preview")
def account_deletion_preview(user: User) -> dict[str, Any]:
    """Return non-secret blockers and deletion scope before an irreversible account deletion."""
    return account_deletion_snapshot(int(user["id"]))


@_app.delete("/api/privacy/account")
async def delete_account(request: AccountDeleteRequest, response: Response, user: User) -> dict[str, Any]:
    """Permanently delete the authenticated Vexmera account after re-authentication and safety checks."""
    user_id = int(user["id"])
    email = str(user["email"])
    stored = _store.get_user_by_email(email)
    if not stored or not verify_password(request.password, stored["password_salt"], stored["password_hash"]):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    snapshot = account_deletion_snapshot(user_id)
    if not snapshot["allowed"]:
        messages = [str(item["message"]) for item in snapshot["blockers"]]
        raise HTTPException(status_code=409, detail="Account deletion is blocked. " + " ".join(messages))

    revocation = await _revoke_owned_connector_tokens(snapshot["owned_workspaces"])
    try:
        deleted = _delete_local_account(user_id, email)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=409,
            detail="Account deletion conditions changed. Reload the deletion preview and try again.",
        ) from exc

    response.delete_cookie("vezmora_session", path="/")
    return {
        "ok": True,
        "account_deleted": True,
        "local_data_deleted": deleted,
        "provider_token_revocation": revocation,
        "third_party_billing_records_may_be_retained": True,
    }
