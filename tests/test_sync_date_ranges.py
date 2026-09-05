from __future__ import annotations

from datetime import date

from app.connectors import _date_range


def _inclusive_days(start: str, end: str) -> int:
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    return (end_date - start_date).days + 1


def test_pilot_sync_date_ranges_are_exact_and_end_yesterday() -> None:
    expected_end = date.today().fromordinal(date.today().toordinal() - 1).isoformat()

    for days in (7, 30, 90):
        start, end = _date_range(days)
        assert end == expected_end
        assert _inclusive_days(start, end) == days


def test_single_day_sync_range_is_valid() -> None:
    start, end = _date_range(1)
    assert start == end
