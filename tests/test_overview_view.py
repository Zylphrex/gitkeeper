from datetime import datetime, timedelta, timezone

from gitkeeper.github.client import ReviewRecord, ReviewerRequest
from gitkeeper.scoring.calculator import ViewerStatus
from gitkeeper.ui.overview_view import (
    _ci_color,
    _pr_number_markup,
    _relative_time,
    _reviewer_row,
    _reviews_row,
    _viewer_status_row,
)


def test_pr_number_markup_with_url():
    url = "https://github.com/acme/backend/pull/101"
    assert _pr_number_markup(101, url) == (
        f'[link="{url}"][bold cyan]#101[/bold cyan][/link]'
    )


def test_pr_number_markup_without_url():
    expected = "[bold cyan]#101[/bold cyan]"
    assert _pr_number_markup(101, None) == expected
    assert _pr_number_markup(101, "") == expected


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


# ---------- viewer-action status line (tui-review-client delta) ----------

def _status(has_reviewed=False, verdict=None, verdict_at=None, re_review_due=False):
    return ViewerStatus(
        has_reviewed=has_reviewed,
        verdict=verdict,
        verdict_at=verdict_at,
        re_review_due=re_review_due,
    )


def test_viewer_status_row_hidden_when_login_unknown():
    assert _viewer_status_row(None, _status()) is None
    assert _viewer_status_row("", _status()) is None


def test_viewer_status_row_not_reviewed():
    row = _viewer_status_row("octocat", _status())
    assert "not yet reviewed" in row


def _days_ago(days: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days)


def test_viewer_status_row_approved():
    row = _viewer_status_row("octocat", _status(True, "APPROVED", _days_ago(2)))
    assert "approved" in row and "2d ago" in row


def test_viewer_status_row_requested_changes():
    row = _viewer_status_row("octocat", _status(True, "CHANGES_REQUESTED", _days_ago(2)))
    assert "requested changes" in row and "2d ago" in row


def test_viewer_status_row_commented_without_verdict():
    at = datetime(2026, 8, 18, 9, 0, tzinfo=timezone.utc)
    row = _viewer_status_row("octocat", _status(True, None, at))
    assert row is not None
    assert "commented" in row or "not yet reviewed" in row


def test_viewer_status_row_re_review_due_indicator():
    at = datetime(2026, 8, 16, 12, 0, tzinfo=timezone.utc)
    row = _viewer_status_row("octocat", _status(True, "APPROVED", at, re_review_due=True))
    assert "approved" in row
    assert "new pushes since review" in row


def test_viewer_status_row_inline_thread_count():
    row = _viewer_status_row("octocat", _status(), own_thread_count=3)
    assert "3 inline comments" in row


def test_viewer_status_row_draft_count():
    row = _viewer_status_row("octocat", _status(), draft_count=2)
    assert "2 drafts pending" in row