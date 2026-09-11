from __future__ import annotations

import httpx

from app.google_ads_diagnostics import _google_ads_error_summary


def _response(payload: object) -> httpx.Response:
    return httpx.Response(
        400,
        json=payload,
        request=httpx.Request("POST", "https://googleads.googleapis.com/v25/customers/1/googleAds:searchStream"),
    )


def test_non_object_payload_is_ignored() -> None:
    assert _google_ads_error_summary(_response(["unexpected"])) is None


def test_non_object_error_is_ignored() -> None:
    assert _google_ads_error_summary(_response({"error": "unexpected"})) is None


def test_non_list_nested_errors_do_not_break_safe_summary() -> None:
    response = _response(
        {
            "error": {
                "status": "PERMISSION_DENIED",
                "message": "Developer token lacks access",
                "details": [
                    {
                        "requestId": "request-123",
                        "errors": {"unexpected": "shape"},
                    }
                ],
            }
        }
    )

    summary = _google_ads_error_summary(response)

    assert summary == "PERMISSION_DENIED | Developer token lacks access | request_id=request-123"
