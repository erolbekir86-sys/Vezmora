from __future__ import annotations

import pytest

from scripts import pilot_preflight, preflight_http, public_legal_preflight, public_runtime_preflight


def test_normalize_https_origin_accepts_plain_https_origin():
    assert preflight_http.normalize_https_origin(" HTTPS://VEXMERA.COM/ ") == "https://vexmera.com"


@pytest.mark.parametrize(
    "value",
    [
        "http://vexmera.com",
        "https://user:pass@vexmera.com",
        "https://vexmera.com/path",
        "https://vexmera.com?next=https://example.com",
        "https://vexmera.com#fragment",
        "https://vexmera.com:invalid",
        "",
    ],
)
def test_normalize_https_origin_rejects_ambiguous_targets(value):
    with pytest.raises(ValueError):
        preflight_http.normalize_https_origin(value)


def test_redirect_handler_never_follows_redirects():
    handler = preflight_http._NoRedirectHandler()
    assert handler.redirect_request(None, None, 302, "Found", {}, "https://example.com") is None


def test_public_fetch_rejects_oversized_response(monkeypatch):
    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, size):
            return b"x" * size

    class Opener:
        def open(self, request, timeout):
            return Response()

    monkeypatch.setattr(preflight_http, "build_opener", lambda *handlers: Opener())

    with pytest.raises(RuntimeError, match="response_too_large"):
        preflight_http.get_public_text(
            "https://vexmera.com/health/runtime",
            user_agent="test",
            max_bytes=32,
        )


@pytest.mark.parametrize(
    "builder",
    [
        pilot_preflight.build_live_preflight,
        public_runtime_preflight.build_public_runtime_preflight,
        public_legal_preflight.build_public_legal_preflight,
    ],
)
def test_public_preflights_fail_closed_before_network_for_invalid_origin(monkeypatch, builder):
    def unexpected_network(*args, **kwargs):
        raise AssertionError("network should not be reached")

    monkeypatch.setattr(pilot_preflight, "_get_text", unexpected_network)
    monkeypatch.setattr(public_runtime_preflight, "_get_text", unexpected_network)
    monkeypatch.setattr(public_legal_preflight, "_get_text", unexpected_network)

    result = builder("https://vexmera.com.attacker.example/path")

    assert result["ok"] is False
    assert result["blockers"] == ["invalid_base_url"]
    assert result["checks"] == {}
