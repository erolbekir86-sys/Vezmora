from app.secret_redaction import redact_sensitive_text


def test_redacts_json_quoted_provider_tokens() -> None:
    payload = '{"access_token":"meta-access-secret","refresh_token": "refresh-secret"}'

    redacted = redact_sensitive_text(payload)

    assert "meta-access-secret" not in redacted
    assert "refresh-secret" not in redacted
    assert redacted == '{"access_token":"[REDACTED]","refresh_token": "[REDACTED]"}'


def test_redacts_python_dict_style_secret_fields_without_hiding_safe_context() -> None:
    payload = "{'client_secret': 'client-secret', 'oauth_state': 'state-secret', 'code': 190}"

    redacted = redact_sensitive_text(payload)

    assert "client-secret" not in redacted
    assert "state-secret" not in redacted
    assert "'code': 190" in redacted
    assert redacted.count("[REDACTED]") == 2


def test_redacts_oauth_capabilities_when_embedded_in_url_queries() -> None:
    payload = (
        "callback failed for https://vexmera.example/api/connectors/google/callback"
        "?code=one-time-code&state=oauth-state and provider retry "
        "https://provider.example/token?client_secret=client-secret&access_token=access-secret"
    )

    redacted = redact_sensitive_text(payload)

    for secret in ("one-time-code", "oauth-state", "client-secret", "access-secret"):
        assert secret not in redacted
    assert "?code=[REDACTED]&state=[REDACTED]" in redacted
    assert "?client_secret=[REDACTED]&access_token=[REDACTED]" in redacted


def test_redacts_app_capabilities_when_embedded_in_url_queries() -> None:
    payload = (
        "https://vexmera.example/?reset=reset-secret&invite=invite-secret "
        "and https://vexmera.example/?billing=success&session_id=checkout-session-secret"
    )

    redacted = redact_sensitive_text(payload)

    for secret in ("reset-secret", "invite-secret", "checkout-session-secret"):
        assert secret not in redacted
    assert "?reset=[REDACTED]&invite=[REDACTED]" in redacted
    assert "?billing=success&session_id=[REDACTED]" in redacted


def test_redacts_authorization_cookie_and_session_fields() -> None:
    payload = (
        "Authorization: Basic dXNlcjpzZWNyZXQ=; "
        "Cookie: vezmora_session=session-cookie-secret; theme=dark; "
        "vezmora_session=raw-session-secret"
    )

    redacted = redact_sensitive_text(payload)

    for secret in ("dXNlcjpzZWNyZXQ=", "session-cookie-secret", "raw-session-secret"):
        assert secret not in redacted
    assert "Authorization: [REDACTED]" in redacted
    assert "Cookie: [REDACTED]" in redacted
    assert "vezmora_session=[REDACTED]" in redacted


def test_redacts_proxy_authorization_and_set_cookie_fields() -> None:
    payload = (
        "Proxy-Authorization: Basic cHJveHk6c2VjcmV0; "
        "Set-Cookie: vezmora_session=set-cookie-secret; Path=/; HttpOnly"
    )

    redacted = redact_sensitive_text(payload)

    assert "cHJveHk6c2VjcmV0" not in redacted
    assert "set-cookie-secret" not in redacted
    assert "Proxy-Authorization: [REDACTED]" in redacted
    assert "Set-Cookie: [REDACTED]" in redacted


def test_plain_non_url_code_and_state_context_remain_visible() -> None:
    payload = "provider error code: 190; state: disconnected"

    assert redact_sensitive_text(payload) == payload
