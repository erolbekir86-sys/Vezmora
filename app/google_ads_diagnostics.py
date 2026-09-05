from __future__ import annotations

import os
import re

import httpx

from . import connectors as _connectors


_original_sync_google = _connectors.sync_google

_SENSITIVE_ENV_NAMES = (
    "GOOGLE_ADS_DEVELOPER_TOKEN",
    "GOOGLE_CLIENT_SECRET",
    "META_APP_SECRET",
    "OPENAI_API_KEY",
    "STRIPE_SECRET_KEY",
    "CRON_SECRET",
    "VEZMORA_ENCRYPTION_KEY",
)

_SENSITIVE_INLINE_PATTERNS = (
    re.compile(r"(?i)(bearer\s+)[^\s,;|]+"),
    re.compile(r"(?i)((?:developer[-_ ]?token|access[-_ ]?token|refresh[-_ ]?token|client[-_ ]?secret|api[-_ ]?key)\s*[:=]\s*)[^\s,;|]+"),
)


def _redact_sensitive_text(value: object) -> str:
    """Redact credentials from upstream diagnostic text before it becomes user-visible."""
    text = str(value)
    for name in _SENSITIVE_ENV_NAMES:
        secret = (os.getenv(name) or "").strip()
        if secret:
            text = text.replace(secret, "[REDACTED]")
    for pattern in _SENSITIVE_INLINE_PATTERNS:
        text = pattern.sub(r"\1[REDACTED]", text)
    return text


def _google_ads_error_summary(response: httpx.Response) -> str | None:
    """Return safe Google Ads error metadata without exposing credentials."""
    try:
        payload = response.json() or {}
    except Exception:
        return None

    error = payload.get("error") or {}
    parts: list[str] = []

    status = error.get("status")
    message = error.get("message")
    if status:
        parts.append(_redact_sensitive_text(status))
    if message:
        parts.append(_redact_sensitive_text(message))

    request_id = None
    google_error_code = None
    google_error_message = None
    for detail in error.get("details") or []:
        if not isinstance(detail, dict):
            continue
        request_id = request_id or detail.get("requestId")
        errors = detail.get("errors") or []
        if errors and isinstance(errors[0], dict):
            first = errors[0]
            error_code = first.get("errorCode") or {}
            if isinstance(error_code, dict) and error_code:
                key, value = next(iter(error_code.items()))
                google_error_code = f"{key}={value}"
            google_error_message = first.get("message")
            break

    if google_error_code:
        parts.append(_redact_sensitive_text(google_error_code))
    if google_error_message and google_error_message != message:
        parts.append(_redact_sensitive_text(google_error_message))
    if request_id:
        parts.append(f"request_id={_redact_sensitive_text(request_id)}")

    summary = " | ".join(part for part in parts if part)
    return summary[:900] if summary else None


async def _diagnose_google_ads_failure(workspace_id: int) -> str | None:
    connector = _connectors.get_connector(workspace_id, "google", include_secret=True)
    if not connector or connector.get("status") != "connected":
        return None

    metadata = connector.get("metadata") or {}
    customer_id = "".join(ch for ch in str(metadata.get("ads_customer_id") or "") if ch.isdigit())
    developer_token = (os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN") or "").strip()
    if not customer_id or not developer_token:
        return None

    try:
        access_token, _ = await _connectors._refresh_google_access_token(workspace_id, connector)
        api_version = (os.getenv("GOOGLE_ADS_API_VERSION") or "v25").strip()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "developer-token": developer_token,
        }
        login_customer_id = (os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID") or "").strip()
        if login_customer_id:
            headers["login-customer-id"] = "".join(ch for ch in login_customer_id if ch.isdigit())

        # Small read-only probe. It performs no mutation and requests no campaign changes.
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"https://googleads.googleapis.com/{api_version}/customers/{customer_id}/googleAds:searchStream",
                headers=headers,
                json={"query": "SELECT customer.id FROM customer LIMIT 1"},
            )
        if response.status_code < 400:
            return None
        return _google_ads_error_summary(response)
    except Exception:
        # Diagnostics must never turn a normal sync failure into a crash.
        return None


async def sync_google_with_diagnostics(workspace_id: int, days: int = 7) -> dict[str, object]:
    result = await _original_sync_google(workspace_id, days)
    warnings = result.get("warnings")
    if not isinstance(warnings, list):
        return result

    generic_index = next(
        (
            index
            for index, warning in enumerate(warnings)
            if isinstance(warning, str) and warning.startswith("Google Ads sync failed (")
        ),
        None,
    )
    if generic_index is None:
        return result

    detail = await _diagnose_google_ads_failure(workspace_id)
    if detail:
        warnings[generic_index] = f"{warnings[generic_index]}: {detail}"
        _connectors.update_connector_metadata(
            workspace_id,
            "google",
            {"last_sync": result},
        )
    return result


_connectors.sync_google = sync_google_with_diagnostics
