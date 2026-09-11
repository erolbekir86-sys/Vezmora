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
