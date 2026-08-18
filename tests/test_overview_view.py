from datetime import datetime, timezone

from gitkeeper.github.client import ReviewRecord, ReviewerRequest
from gitkeeper.ui.overview_view import (
    _ci_color,
    _relative_time,
    _reviewer_row,
    _reviews_row,
)


def test_ci_color_mapping():
    assert _ci_color("SUCCESS") == "green"
    assert _ci_color("ERROR") == "red"
    assert _ci_color("FAILURE") == "red"
    assert _ci_color("PENDING") == "yellow"
    assert _ci_color("EXPECTED") == "yellow"
    assert _ci_color(None) == "white"
    assert _ci_color("UNKNOWN") == "white"


def test_relative_time_formats():
    now = datetime(2026, 8, 18, 12, 0, tzinfo=timezone.utc)

    assert _relative_time(None, now=now) is None
    assert _relative_time("not-a-date", now=now) is None
    assert _relative_time("2026-08-18T11:59:30Z", now=now) == "just now"
    assert _relative_time("2026-08-18T11:55:00Z", now=now) == "5m ago"
    assert _relative_time("2026-08-18T09:00:00Z", now=now) == "3h ago"
    assert _relative_time("2026-08-16T12:00:00Z", now=now) == "2d ago"
    assert _relative_time("2026-07-28T12:00:00Z", now=now) == "3w ago"
    assert _relative_time("2026-06-18T12:00:00Z", now=now) == "2mo ago"


def test_relative_time_handles_naive_timestamps():
    now = datetime(2026, 8, 18, 12, 0, tzinfo=timezone.utc)
    assert _relative_time("2026-08-18T09:00:00", now=now) == "3h ago"


def test_reviewer_row_caps_at_three():
    assert _reviewer_row([]) is None

    three = [
        ReviewerRequest("core-team", is_team=True),
        ReviewerRequest("bob", is_team=False),
        ReviewerRequest("sam", is_team=False),
    ]
    assert _reviewer_row(three) == "Reviewers: [dim]core-team, @bob, @sam[/dim]"

    four = three + [ReviewerRequest("lea", is_team=False)]
    assert _reviewer_row(four) == "Reviewers: [dim]core-team, @bob, @sam, +1 more[/dim]"


def test_reviews_row_summarizes_by_state():
    assert _reviews_row([]) is None

    reviews = [
        ReviewRecord("bob", "APPROVED", None),
        ReviewRecord("sam", "APPROVED", None),
        ReviewRecord("lea", "CHANGES_REQUESTED", None),
    ]
    assert _reviews_row(reviews) == "Reviews: [dim]2 ✓ · 1 ✗[/dim]"