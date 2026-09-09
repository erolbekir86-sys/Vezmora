from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

from app import connector_empty_states
from app import connectors
from app import meta_read_reliability as reliability


class FakeResponse:
    def __init__(self, status_code: int, payload: object, headers: dict[str, str] | None = None):
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, responses: list[FakeResponse]):
        self.responses = list(responses)
        self.calls: list[tuple[str, object]] = []

    async def get(self, url, params=None):
        self.calls.append((str(url), params))
        if not self.responses:
            raise AssertionError("Unexpected extra Meta request")
        return self.responses.pop(0)


def test_meta_insights_follows_all_pages_and_does_not_reappend_first_page_params(monkeypatch):
    monkeypatch.setenv("VEZMORA_META_MAX_INSIGHTS_PAGES", "10")
    first = FakeResponse(
        200,
        {
            "data": [{"date_start": "2026-09-08", "campaign_id": "1"}],
            "paging": {"next": "https://graph.facebook.com/v24.0/next?after=cursor&access_token=private"},
        },
    )
    second = FakeResponse(
        200,
        {"data": [{"date_start": "2026-09-08", "campaign_id": "2"}], "paging": {}},
    )
    client = FakeClient([first, second])

    rows, pages = asyncio.run(
        reliability._meta_insight_rows(
            client,
            "https://graph.facebook.com/v24.0/act_1/insights",
            {"access_token": "private", "limit": 100},
        )
    )

    assert pages == 2
    assert [row["campaign_id"] for row in rows] == ["1", "2"]
    assert client.calls[0][1] == {"access_token": "private", "limit": 100}
    assert client.calls[1][1] is None


def test_meta_get_retries_429_then_succeeds_without_unbounded_loop(monkeypatch):
    slept: list[float] = []

    async def no_sleep(delay: float):
        slept.append(delay)

    monkeypatch.setattr(reliability.asyncio, "sleep", no_sleep)
    client = FakeClient(
        [
            FakeResponse(429, {"error": {"code": 4}}, {"Retry-After": "1"}),
            FakeResponse(503, {"error": {}}),
            FakeResponse(200, {"data": []}),
        ]
    )

    response = asyncio.run(reliability._meta_get(client, "https://graph.facebook.com/read", max_attempts=4))

    assert response.status_code == 200
    assert len(client.calls) == 3
    assert slept == [1.0, 1.0]


def test_meta_error_mapping_is_actionable_and_does_not_surface_raw_provider_message():
    response = FakeResponse(
        400,
        {
            "error": {
                "code": 190,
                "message": "OAuth token private-secret-value is invalid",
            }
        },
    )

    detail = reliability._meta_error_detail(response, "Meta insights sync")

    assert "Reconnect Meta" in detail
    assert "private-secret-value" not in detail
    assert "OAuth token" not in detail


def test_meta_pagination_fails_closed_on_repeated_next_url(monkeypatch):
    monkeypatch.setenv("VEZMORA_META_MAX_INSIGHTS_PAGES", "10")
    next_url = "https://graph.facebook.com/v24.0/next?after=same"
    client = FakeClient(
        [
            FakeResponse(200, {"data": [], "paging": {"next": next_url}}),
            FakeResponse(200, {"data": [], "paging": {"next": next_url}}),
        ]
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            reliability._meta_insight_rows(
                client,
                "https://graph.facebook.com/v24.0/act_1/insights",
                {"access_token": "private"},
            )
        )

    assert exc_info.value.status_code == 502
    assert "repeated page" in str(exc_info.value.detail)


def test_meta_pagination_fails_closed_instead_of_writing_partial_unbounded_result(monkeypatch):
    monkeypatch.setenv("VEZMORA_META_MAX_INSIGHTS_PAGES", "1")
    client = FakeClient(
        [FakeResponse(200, {"data": [{"campaign_id": "1"}], "paging": {"next": "https://graph.facebook.com/next"}})]
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            reliability._meta_insight_rows(
                client,
                "https://graph.facebook.com/v24.0/act_1/insights",
                {"access_token": "private"},
            )
        )

    assert exc_info.value.status_code == 502
    assert "safe pagination limit" in str(exc_info.value.detail)


def test_meta_row_deduplication_prevents_duplicate_daily_aggregation():
    rows = reliability._dedupe_rows(
        [
            {"date_start": "2026-09-08", "campaign_id": "1", "clicks": "10"},
            {"date_start": "2026-09-08", "campaign_id": "1", "clicks": "11"},
            {"date_start": "2026-09-08", "campaign_id": "2", "clicks": "2"},
        ]
    )
    assert len(rows) == 2
    by_id = {row["campaign_id"]: row for row in rows}
    assert by_id["1"]["clicks"] == "11"


def test_meta_reliable_sync_is_preserved_under_existing_empty_state_wrapper():
    """Reliability must be the read base while existing UX wrappers remain intact."""
    reliability.install_meta_read_reliability()

    assert connector_empty_states._original_sync_meta is reliability.sync_meta_reliable
    assert connectors.sync_meta is connector_empty_states.sync_meta_with_empty_state
