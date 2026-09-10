from __future__ import annotations

import asyncio

import httpx

from app import connector_empty_states
from app import connectors
from app import google_ads_diagnostics
from app import google_read_reliability as reliability
from app import main as app_main


class FakeResponse:
    def __init__(self, status_code: int, payload: object, headers: dict[str, str] | None = None):
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class FakeClient:
    def __init__(self, responses: list[object]):
        self.responses = list(responses)
        self.calls: list[dict[str, object]] = []

    async def post(self, url, headers=None, json=None, data=None):
        self.calls.append({"url": str(url), "headers": headers, "json": json, "data": data})
        if not self.responses:
            raise AssertionError("Unexpected extra Google request")
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def test_google_post_retries_transient_statuses_then_succeeds(monkeypatch):
    slept: list[float] = []

    async def no_sleep(delay: float):
        slept.append(delay)

    monkeypatch.setattr(reliability.asyncio, "sleep", no_sleep)
    client = FakeClient(
        [
            FakeResponse(429, {"error": {}}, {"Retry-After": "1"}),
            FakeResponse(503, {"error": {}}),
            FakeResponse(200, {"rows": []}),
        ]
    )

    response = asyncio.run(
        reliability._google_post(
            client,
            "https://google.example/read",
            json_body={"read": True},
            max_attempts=4,
        )
    )

    assert response.status_code == 200
    assert len(client.calls) == 3
    assert slept == [1.0, 1.0]
    assert all(call["json"] == {"read": True} for call in client.calls)


def test_google_post_retries_transport_error_then_succeeds(monkeypatch):
    slept: list[float] = []

    async def no_sleep(delay: float):
        slept.append(delay)

    monkeypatch.setattr(reliability.asyncio, "sleep", no_sleep)
    client = FakeClient(
        [
            httpx.ConnectError("temporary network failure"),
            FakeResponse(200, {"rows": []}),
        ]
    )

    response = asyncio.run(reliability._google_post(client, "https://google.example/read", max_attempts=3))

    assert response.status_code == 200
    assert len(client.calls) == 2
    assert slept == [0.5]


def test_google_post_does_not_retry_non_transient_client_error(monkeypatch):
    slept: list[float] = []

    async def no_sleep(delay: float):
        slept.append(delay)

    monkeypatch.setattr(reliability.asyncio, "sleep", no_sleep)
    client = FakeClient([FakeResponse(400, {"error": {"status": "INVALID_ARGUMENT"}})])

    response = asyncio.run(reliability._google_post(client, "https://google.example/read", max_attempts=4))

    assert response.status_code == 400
    assert len(client.calls) == 1
    assert slept == []


def test_google_ads_payload_validation_is_fail_closed_before_writes():
    valid = FakeResponse(
        200,
        [
            {"results": [{"segments": {"date": "2026-09-09"}, "campaign": {"id": "1"}}]},
            {"results": [{"segments": {"date": "2026-09-09"}, "campaign": {"id": "2"}}]},
        ],
    )
    malformed_top_level = FakeResponse(200, {"results": []})
    malformed_page = FakeResponse(200, [{"results": "not-a-list"}])
    malformed_row = FakeResponse(200, [{"results": ["not-a-row"]}])

    rows = reliability._safe_ads_results(valid)

    assert rows is not None
    assert [row["campaign"]["id"] for row in rows] == ["1", "2"]
    assert reliability._safe_ads_results(malformed_top_level) is None
    assert reliability._safe_ads_results(malformed_page) is None
    assert reliability._safe_ads_results(malformed_row) is None


def test_google_payload_helpers_do_not_raise_on_invalid_json():
    invalid = FakeResponse(200, ValueError("private provider body"))

    assert reliability._safe_dict_payload(invalid) is None
    assert reliability._safe_ads_results(invalid) is None


def test_google_reliability_remains_base_of_existing_wrapper_chain():
    """Reliability is base, diagnostics is middle, empty-state UX remains outermost."""
    reliability.install_google_read_reliability()

    assert google_ads_diagnostics._original_sync_google is reliability.sync_google_reliable
    assert connector_empty_states._original_sync_google is google_ads_diagnostics.sync_google_with_diagnostics
    assert connectors.sync_google is connector_empty_states.sync_google_with_empty_state
    assert app_main.sync_google is connector_empty_states.sync_google_with_empty_state
    assert connectors._refresh_google_access_token is reliability.refresh_google_access_token_reliable
    assert connectors._google_read_post is reliability._google_post


def test_google_reliability_layer_contains_no_execution_or_scope_changes():
    source = open(reliability.__file__, encoding="utf-8").read()

    forbidden = (
        "GOOGLE_SCOPES =",
        "ads_management",
        "VEZMORA_EXECUTION_ENABLED",
        "VEZMORA_AUTOPILOT_EXECUTION_ENABLED",
        "pause_campaign",
        "mutate",
    )
    for marker in forbidden:
        assert marker not in source
