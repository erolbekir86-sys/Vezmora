from __future__ import annotations

import json
from pathlib import Path


def test_vercel_config_sets_minimal_csp_without_restricting_app_assets():
    config = json.loads(Path("vercel.json").read_text(encoding="utf-8"))

    header_rules = config.get("headers") or []
    global_rule = next((rule for rule in header_rules if rule.get("source") == "/(.*)"), None)

    assert global_rule is not None
    headers = {item["key"].lower(): item["value"] for item in global_rule.get("headers", [])}
    assert headers["content-security-policy"] == "base-uri 'self'; object-src 'none'"

    # Keep this intentionally minimal for Private Beta. These directives harden
    # injected <base> and plugin/object content without changing script/style,
    # API, OAuth, analytics, or payment origins.
    csp = headers["content-security-policy"]
    assert "default-src" not in csp
    assert "script-src" not in csp
    assert "style-src" not in csp
    assert "connect-src" not in csp
