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

_SENSITIVE_INLINE_PATTERNS = (
    re.compile(r"(?i)(bearer\s+)[^\s,;|]+"),
    re.compile(
        r"(?i)((?:developer[-_ ]?token|access[-_ ]?token|refresh[-_ ]?token|client[-_ ]?secret|"
        r"api[-_ ]?key|webhook[-_ ]?secret|password|auth[-_ ]?token)\s*[:=]\s*)[^\s,;|]+"
    ),
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
