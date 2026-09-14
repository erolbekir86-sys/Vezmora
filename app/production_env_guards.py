from __future__ import annotations

import os
from urllib.parse import urlsplit


_PRIVATE_BETA_DISABLED_FLAGS = (
    "VEZMORA_DEV_SHOW_TOKENS",
    "VEZMORA_EXECUTION_ENABLED",
    "VEZMORA_AUTOPILOT_EXECUTION_ENABLED",
    "VEZMORA_ENABLE_META_EXECUTION_SCOPE",
)
_LEGACY_ONLY_PRICE_ENV = ("STRIPE_PRICE_STARTER", "STRIPE_PRICE_SCALE")
_OAUTH_CALLBACK_PATHS = {
    "GOOGLE_REDIRECT_URI": "/api/connectors/google/callback",
    "META_REDIRECT_URI": "/api/connectors/meta/callback",
}


def _plain_https_origin(value: str) -> str | None:
    if not value:
        return None
    parts = urlsplit(value)
    if parts.scheme.lower() != "https" or not parts.netloc:
        return None
    if parts.username is not None or parts.password is not None:
        return None
    if parts.path not in {"", "/"} or parts.query or parts.fragment:
        return None
    return f"https://{parts.netloc}"


def apply_production_env_guards() -> None:
    """Fail closed for unsafe Private Beta-only overrides on Vercel.

    Local development can still opt into explicit test behavior. On Vercel,
    however, stale or accidental environment overrides must not expose reset or
    invite tokens, unlock external ad mutations, enable autonomous execution,
    request Meta's ads_management scope, allow insecure/mismatched absolute
    origins, or revive historical Stripe price variable names.
    """
    if not os.getenv("VERCEL"):
        return

    for name in _PRIVATE_BETA_DISABLED_FLAGS:
        os.environ[name] = "false"

    # Password-reset, invite and billing return links use VEZMORA_APP_URL. Require
    # one plain HTTPS origin rather than merely an https:// prefix. Removing an
    # unsafe value makes runtime/preflight checks and downstream link builders fail
    # closed instead of accepting credentials, paths, queries or fragments.
    raw_app_url = (os.getenv("VEZMORA_APP_URL") or "").strip()
    app_url = _plain_https_origin(raw_app_url) or ""
    if raw_app_url and not app_url:
        os.environ.pop("VEZMORA_APP_URL", None)

    # OAuth authorization codes and state are capabilities. A production OAuth
    # callback must land on the exact canonical Vexmera origin and provider path.
    # If the app origin is missing/unsafe or a redirect differs, make that
    # connector unconfigured in this process rather than constructing a risky
    # authorization request. External Google/Meta settings are never mutated.
    for env_name, callback_path in _OAUTH_CALLBACK_PATHS.items():
        configured_redirect = (os.getenv(env_name) or "").strip()
        expected_redirect = f"{app_url}{callback_path}" if app_url else ""
        if configured_redirect and configured_redirect != expected_redirect:
            os.environ.pop(env_name, None)

    # Current billing uses only STRIPE_PRICE_START/GROWTH/PRO. Historical
    # STARTER/SCALE aliases must not be synthesized in production because they
    # can make stale diagnostics or future code paths mistake old catalog state
    # for the verified Start/Growth/Pro model. Growth already keeps its canonical
    # variable name and current price variables are intentionally left untouched.
    for legacy_name in _LEGACY_ONLY_PRICE_ENV:
        os.environ.pop(legacy_name, None)
