from __future__ import annotations

import os
import re

SENSITIVE_ENV_NAMES = (
    "GOOGLE_ADS_DEVELOPER_TOKEN",
    "GOOGLE_CLIENT_SECRET",
    "META_APP_SECRET",
    "OPENAI_API_KEY",
    "STRIPE_SECRET_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "SMTP_PASSWORD",
    "TURSO_AUTH_TOKEN",
    "DATABASE_URL",
    "POSTGRES_URL",
    "TURSO_DATABASE_URL",
    "CRON_SECRET",
    "VEZMORA_SECRET_KEY",
    # Retained for compatibility with older deployments that used this name.
    "VEZMORA_ENCRYPTION_KEY",
)

_SENSITIVE_FIELD_NAMES = (
    r"developer[-_ ]?token|access[-_ ]?token|refresh[-_ ]?token|client[-_ ]?secret|"
    r"api[-_ ]?key|webhook[-_ ]?secret|password|auth[-_ ]?token|session[-_ ]?token|"
    r"reset[-_ ]?token|invite[-_ ]?token|oauth[-_ ]?state"
)

_SENSITIVE_INLINE_PATTERNS = (
    re.compile(r"(?i)(bearer\s+)[^\s,;|]+"),
    # OAuth callback/provider URLs can surface in transport diagnostics. Query
    # names such as `code` and `state` are too generic to redact everywhere, so
    # treat them as sensitive only when they appear as URL query parameters.
    re.compile(r"(?i)([?&](?:code|state|access_token|refresh_token|client_secret)=)[^&#\s]+"),
    # JSON and Python-dict style diagnostics are common provider-error shapes.
    # Keep the key/quote formatting while replacing only the sensitive value.
    re.compile(rf"(?i)([\"']?(?:{_SENSITIVE_FIELD_NAMES})[\"']?\s*:\s*[\"'])[^\"']+(?=[\"'])"),
    re.compile(rf"(?i)((?:{_SENSITIVE_FIELD_NAMES})\s*[:=]\s*)[^\s,;|]+"),
)


def redact_sensitive_text(value: object) -> str:
    """Redact configured and inline credentials before text is exposed or persisted."""
    text = str(value)
    for name in SENSITIVE_ENV_NAMES:
        secret = (os.getenv(name) or "").strip()
        if secret:
            text = text.replace(secret, "[REDACTED]")
    for pattern in _SENSITIVE_INLINE_PATTERNS:
        text = pattern.sub(r"\1[REDACTED]", text)
    return text
