from rich.console import Console
from gitkeeper.github.client import PullRequestData
from gitkeeper.scoring.pipeline import ScoredPullRequest
from gitkeeper.scoring.calculator import ScoreBreakdown
from gitkeeper.ui.table import render_pull_requests_table


def _make_scored_pr(number: int, url: str) -> ScoredPullRequest:
    pr = PullRequestData(
        id=f"PR_{number}",
        number=number,
        title="Test PR",
        url=url,
        repo_name_with_owner="acme/backend",
        author="alice",
        is_draft=False,
        state="OPEN",
        created_at="2026-08-14T10:00:00Z",
        updated_at="2026-08-15T12:00:00Z",
        additions=10,
        deletions=2,
        changed_files_count=1,
        ci_status="SUCCESS",
    )
    score = ScoreBreakdown(
        affinity_points=50.0,
        assignment_points=30.0,
        urgency_points=10.0,
        total_score=90,
        rationale="Author teammate",
    )
    return ScoredPullRequest(pr=pr, is_actionable=True, score=score)


def test_render_pull_requests_table_with_hyperlink():
    console = Console(record=True, width=120)
    scored_pr = _make_scored_pr(123, "https://github.com/acme/backend/pull/123")

    render_pull_requests_table([scored_pr], console=console)
    output = console.export_text()

    assert "#123" in output
    assert "acme/backend" in output
    assert "@alice" in output
    assert "Test PR" in output


def test_render_pull_requests_table_without_url():
    console = Console(record=True, width=120)
    scored_pr = _make_scored_pr(456, "")

    render_pull_requests_table([scored_pr], console=console)
    output = console.export_text()

    assert "#456" in output
