from __future__ import annotations

from scripts import public_legal_preflight


def test_public_legal_preflight_passes_when_homepage_links_are_present(monkeypatch):
    responses = {
        "https://vexmera.com/": (200, '<a href="/privacy">Integritet</a><a href="/terms">Villkor</a>'),
        "https://vexmera.com/privacy": (200, "Integritetspolicy Google API Services User Data Policy"),
        "https://vexmera.com/terms": (200, "Terms of Service Vexmera"),
    }
    monkeypatch.setattr(public_legal_preflight, "_get_text", lambda url, timeout=8.0: responses[url])

    result = public_legal_preflight.build_public_legal_preflight("https://vexmera.com/")

    assert result["ok"] is True
    assert result["blockers"] == []
    assert result["checks"]["homepage"]["privacy_linked"] is True
    assert result["checks"]["homepage"]["terms_linked"] is True


def test_public_legal_preflight_blocks_if_privacy_is_not_linked(monkeypatch):
    responses = {
        "https://vexmera.com/": (200, '<a href="/terms">Villkor</a>'),
        "https://vexmera.com/privacy": (200, "Integritetspolicy Google API Services User Data Policy"),
        "https://vexmera.com/terms": (200, "Terms of Service Vexmera"),
    }
    monkeypatch.setattr(public_legal_preflight, "_get_text", lambda url, timeout=8.0: responses[url])

    result = public_legal_preflight.build_public_legal_preflight("https://vexmera.com")

    assert result["ok"] is False
    assert "privacy_not_linked_from_homepage" in result["blockers"]


def test_public_legal_preflight_blocks_if_terms_are_not_linked(monkeypatch):
    responses = {
        "https://vexmera.com/": (200, '<a href="/privacy">Integritet</a>'),
        "https://vexmera.com/privacy": (200, "Integritetspolicy Google API Services User Data Policy"),
        "https://vexmera.com/terms": (200, "Terms of Service Vexmera"),
    }
    monkeypatch.setattr(public_legal_preflight, "_get_text", lambda url, timeout=8.0: responses[url])

    result = public_legal_preflight.build_public_legal_preflight("https://vexmera.com")

    assert result["ok"] is False
    assert "terms_not_linked_from_homepage" in result["blockers"]


def test_public_legal_preflight_distinguishes_page_content_regression(monkeypatch):
    responses = {
        "https://vexmera.com/": (200, '<a href="/privacy">Integritet</a><a href="/terms">Villkor</a>'),
        "https://vexmera.com/privacy": (200, "Integritetspolicy"),
        "https://vexmera.com/terms": (200, "Terms of Service Vexmera"),
    }
    monkeypatch.setattr(public_legal_preflight, "_get_text", lambda url, timeout=8.0: responses[url])

    result = public_legal_preflight.build_public_legal_preflight("https://vexmera.com")

    assert result["ok"] is False
    assert "privacy_page_unexpected_content" in result["blockers"]


def test_public_legal_preflight_handles_unreachable_homepage(monkeypatch):
    responses = {
        "https://vexmera.com/privacy": (200, "Integritetspolicy Google API Services User Data Policy"),
        "https://vexmera.com/terms": (200, "Terms of Service Vexmera"),
    }

    def fake_get(url, timeout=8.0):
        if url == "https://vexmera.com/":
            raise RuntimeError("request_failed:URLError")
        return responses[url]

    monkeypatch.setattr(public_legal_preflight, "_get_text", fake_get)

    result = public_legal_preflight.build_public_legal_preflight("https://vexmera.com")

    assert result["ok"] is False
    assert result["blockers"].count("homepage_unreachable") == 1
