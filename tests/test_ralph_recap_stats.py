"""Tests for pure helpers in discord-ralph-recap/scripts/stats.py."""

from __future__ import annotations

import datetime as dt

from conftest import ralph_stats as rs

UTC = dt.timezone.utc


def _at(day: int, hour: int = 12) -> dt.datetime:
    return dt.datetime(2026, 6, day, hour, tzinfo=UTC)


# ---------- parse_iso ----------


def test_parse_iso_handles_trailing_z() -> None:
    parsed = rs.parse_iso("2026-06-27T08:30:00Z")
    assert parsed == dt.datetime(2026, 6, 27, 8, 30, tzinfo=UTC)


# ---------- normalize_verdict ----------


def test_normalize_verdict_returns_none_without_verdict_line() -> None:
    assert rs.normalize_verdict("Looks great, merging!") is None


def test_normalize_verdict_detects_lgtm() -> None:
    assert rs.normalize_verdict("Nice work.\nVerdict: LGTM") == rs.LGTM


def test_normalize_verdict_changes_requested_beats_lgtm_mention() -> None:
    body = "This is not yet LGTM.\nVerdict: CHANGES_REQUESTED"
    assert rs.normalize_verdict(body) == rs.CHANGES_REQUESTED


def test_normalize_verdict_defaults_to_comments() -> None:
    assert rs.normalize_verdict("Some notes.\nVerdict: COMMENTS") == rs.COMMENTS


# ---------- iterations_before_lgtm ----------


def test_iterations_before_lgtm_counts_rounds() -> None:
    verdicts = [rs.CHANGES_REQUESTED, rs.COMMENTS, rs.LGTM]
    assert rs.iterations_before_lgtm(verdicts) == 2


def test_iterations_before_lgtm_zero_for_clean_merge() -> None:
    assert rs.iterations_before_lgtm([rs.LGTM]) == 0


def test_iterations_before_lgtm_none_when_never_lgtm() -> None:
    assert rs.iterations_before_lgtm([rs.CHANGES_REQUESTED, rs.COMMENTS]) is None


# ---------- merge_rate ----------


def test_merge_rate_empty() -> None:
    rate = rs.merge_rate([], now=_at(27))
    assert rate["total"] == 0.0
    assert rate["per_day"] == 0.0


def test_merge_rate_spans_first_merge_to_now() -> None:
    merged = [_at(20), _at(22), _at(24)]
    rate = rs.merge_rate(merged, now=_at(30))
    assert rate["total"] == 3.0
    assert rate["span_days"] == 10.0
    assert rate["per_day"] == 0.3


def test_merge_rate_last_7_days_window() -> None:
    merged = [_at(1), _at(25), _at(27)]
    rate = rs.merge_rate(merged, now=_at(28))
    assert rate["last_7_days"] == 2.0


# ---------- time_to_merge_stats ----------


def test_time_to_merge_stats() -> None:
    out = rs.time_to_merge_stats([1.0, 3.0, 5.0])
    assert out["median"] == 3.0
    assert out["fastest"] == 1.0
    assert out["slowest"] == 5.0
    assert out["mean"] == 3.0


# ---------- iteration_stats ----------


def test_iteration_stats_clean_merge_rate() -> None:
    out = rs.iteration_stats([0, 0, 2, 4])
    assert out["clean_merge_rate"] == 0.5
    assert out["max"] == 4.0
    assert out["sample"] == 4.0


def test_iteration_stats_empty() -> None:
    out = rs.iteration_stats([])
    assert out["sample"] == 0.0


# ---------- estimate_remaining ----------


def test_estimate_remaining_projects_eta() -> None:
    est = rs.estimate_remaining(10, 2.0, now=_at(1))
    assert est["known"] is True
    assert est["days_remaining"] == 5.0
    assert est["eta"] == _at(6)


def test_estimate_remaining_unknown_when_rate_zero() -> None:
    est = rs.estimate_remaining(10, 0.0, now=_at(1))
    assert est["known"] is False
    assert est["days_remaining"] is None


def test_estimate_remaining_clear_backlog() -> None:
    est = rs.estimate_remaining(0, 2.0, now=_at(1))
    assert est["open_items"] == 0
    assert est["days_remaining"] == 0.0


# ---------- churn_totals ----------


def test_churn_totals_sums_and_nets() -> None:
    out = rs.churn_totals([(10, 3, 2), (5, 5, 1)])
    assert out["additions"] == 15
    assert out["deletions"] == 8
    assert out["net"] == 7
    assert out["files"] == 3


# ---------- busiest_day ----------


def test_busiest_day_picks_max() -> None:
    merged = [_at(20), _at(20), _at(21)]
    result = rs.busiest_day(merged)
    assert result == ("2026-06-20", 2)


def test_busiest_day_none_when_empty() -> None:
    assert rs.busiest_day([]) is None
