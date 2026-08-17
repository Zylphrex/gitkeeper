import pytest
from gitkeeper.config import Config
from gitkeeper.git.decay import PathTouchScore
from gitkeeper.github.client import PullRequestData, PullRequestFile, ReviewRecord, ReviewerRequest
from gitkeeper.repos import RepoLocator
from gitkeeper.scoring.calculator import calculate_relevance_score
from gitkeeper.scoring.gates import is_actionable
from gitkeeper.scoring.pipeline import RelevancePipeline


def test_is_actionable_gates():
    cfg = Config()
    pr_draft = PullRequestData(
        id="1",
        number=1,
        title="WIP",
        url="",
        repo_name_with_owner="org/repo",
        author="alice",
        is_draft=True,
        state="OPEN",
        created_at="",
        updated_at="",
        additions=10,
        deletions=5,
        changed_files_count=1,
        ci_status=None,
    )
    actionable, reason = is_actionable(pr_draft, "octocat", cfg.heuristics)
    assert actionable is False
    assert "draft" in reason

    pr_failing_ci = PullRequestData(
        id="2",
        number=2,
        title="Fix bug",
        url="",
        repo_name_with_owner="org/repo",
        author="alice",
        is_draft=False,
        state="OPEN",
        created_at="",
        updated_at="",
        additions=10,
        deletions=5,
        changed_files_count=1,
        ci_status="FAILURE",
    )
    actionable, reason = is_actionable(pr_failing_ci, "octocat", cfg.heuristics)
    assert actionable is False
    assert "CI" in reason

    pr_already_reviewed = PullRequestData(
        id="3",
        number=3,
        title="Feature",
        url="",
        repo_name_with_owner="org/repo",
        author="alice",
        is_draft=False,
        state="OPEN",
        created_at="",
        updated_at="",
        additions=10,
        deletions=5,
        changed_files_count=1,
        ci_status="SUCCESS",
        reviews=[ReviewRecord(author="octocat", state="APPROVED")],
    )
    actionable, reason = is_actionable(pr_already_reviewed, "octocat", cfg.heuristics)
    assert actionable is False
    assert "APPROVED" in reason


def test_calculate_relevance_score():
    cfg = Config()
    pr = PullRequestData(
        id="1",
        number=10,
        title="Update auth",
        url="",
        repo_name_with_owner="org/repo",
        author="alice",
        is_draft=False,
        state="OPEN",
        created_at="2026-08-10T12:00:00Z",
        updated_at="2026-08-10T12:00:00Z",
        additions=30,
        deletions=10,
        changed_files_count=2,
        ci_status="SUCCESS",
        requested_reviewers=[ReviewerRequest(login_or_slug="octocat", is_team=False)],
        files=[
            PullRequestFile(path="auth.py", additions=20, deletions=5, change_type="MODIFIED"),
            PullRequestFile(path="utils.py", additions=10, deletions=5, change_type="MODIFIED"),
        ],
    )
    touch_scores = [
        PathTouchScore(path="auth.py", touches_recent_90d=3),
        PathTouchScore(path="utils.py", touches_older=1),
    ]

    breakdown = calculate_relevance_score(
        pr=pr,
        touch_scores=touch_scores,
        current_username="octocat",
        heuristics=cfg.heuristics,
        has_local_clone=True,
    )

    # Affinity: auth.py (10) + utils.py (2) = 12
    # Assignment: Direct review = 30
    # Urgency/Size: additions+deletions=40 (<100) -> 10, age > 24h -> 5
    # Total = 12 + 30 + 10 + 5 = 57
    assert breakdown.total_score == 57
    assert "Direct review" in breakdown.rationale
    assert "touched 2/2 files" in breakdown.rationale
    assert "small PR" in breakdown.rationale
