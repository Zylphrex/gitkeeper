import pytest
from datetime import datetime, timezone, timedelta
from gitkeeper.config import Config
from gitkeeper.git.decay import PathTouchScore
from gitkeeper.github.client import PullRequestData, PullRequestFile, ReviewRecord, ReviewerRequest
from gitkeeper.repos import RepoLocator
from gitkeeper.scoring.calculator import TriageTier, assign_triage_tier
from gitkeeper.scoring.gates import is_actionable
from gitkeeper.scoring.pipeline import RelevancePipeline


def make_pr(**overrides) -> PullRequestData:
    defaults = dict(
        id="PR_10",
        number=10,
        title="Update auth",
        url="",
        repo_name_with_owner="org/repo",
        author="alice",
        is_draft=False,
        state="OPEN",
        created_at="2026-08-01T12:00:00Z",
        updated_at="2026-08-10T12:00:00Z",
        additions=30,
        deletions=10,
        changed_files_count=2,
        ci_status="SUCCESS",
        requested_reviewers=[],
        reviews=[],
        files=[
            PullRequestFile(path="auth.py", additions=20, deletions=5, change_type="MODIFIED"),
            PullRequestFile(path="utils.py", additions=10, deletions=5, change_type="MODIFIED"),
        ],
    )
    defaults.update(overrides)
    return PullRequestData(**defaults)


def test_is_actionable_gates():
    cfg = Config()
    pr_draft = make_pr(number=1, is_draft=True)
    actionable, reason = is_actionable(pr_draft, "octocat", cfg.heuristics)
    assert actionable is False
    assert "draft" in reason

    pr_failing_ci = make_pr(number=2, ci_status="FAILURE")
    actionable, reason = is_actionable(pr_failing_ci, "octocat", cfg.heuristics)
    assert actionable is False
    assert "CI" in reason

    pr_already_reviewed = make_pr(number=3, reviews=[ReviewRecord(author="octocat", state="APPROVED")])
    actionable, reason = is_actionable(pr_already_reviewed, "octocat", cfg.heuristics)
    assert actionable is False
    assert "APPROVED" in reason


def test_review_review_carve_out():
    cfg = Config()
    stale = make_pr(
        number=4,
        reviews=[ReviewRecord(author="octocat", state="CHANGES_REQUESTED", submitted_at="2026-08-09T10:00:00Z")],
    )
    actionable, reason = is_actionable(stale, "octocat", cfg.heuristics)
    assert actionable is False

    refreshed = make_pr(
        number=5,
        pushed_at="2026-08-12T10:00:00Z",
        reviews=[ReviewRecord(author="octocat", state="CHANGES_REQUESTED", submitted_at="2026-08-10T10:00:00Z")],
    )
    actionable, reason = is_actionable(refreshed, "octocat", cfg.heuristics)
    assert actionable is True
    assert reason == "re-review"


def test_assign_triage_tier_direct_request():
    cfg = Config()
    pr = make_pr(
        number=1,
        requested_reviewers=[
            ReviewerRequest(login_or_slug="octocat", is_team=False),
            ReviewerRequest(login_or_slug="bob", is_team=False),
        ],
    )
    breakdown = assign_triage_tier(
        pr=pr,
        touch_scores=[],
        current_username="octocat",
        heuristics=cfg.heuristics,
        has_local_clone=True,
    )
    assert breakdown.tier == TriageTier.T1
    assert "directly requested" in breakdown.reasons
    assert breakdown.rationale


def test_assign_triage_tier_0_bottleneck():
    cfg = Config()
    pr = make_pr(
        number=2,
        pushed_at="2026-08-15T09:00:00Z",
        requested_reviewers=[
            ReviewerRequest(login_or_slug="octocat", is_team=False),
            ReviewerRequest(login_or_slug="bob", is_team=False),
        ],
        reviews=[ReviewRecord(author="bob", state="APPROVED", submitted_at="2026-08-14T09:00:00Z")],
    )
    breakdown = assign_triage_tier(
        pr=pr,
        touch_scores=[],
        current_username="octocat",
        heuristics=cfg.heuristics,
        has_local_clone=True,
    )
    assert breakdown.tier == TriageTier.T0
    assert any("bottleneck" in reason for reason in breakdown.reasons)


def test_assign_triage_tier_0_only_reviewer():
    cfg = Config()
    pr = make_pr(
        number=3,
        requested_reviewers=[ReviewerRequest(login_or_slug="octocat", is_team=False)],
    )
    breakdown = assign_triage_tier(
        pr=pr,
        touch_scores=[],
        current_username="octocat",
        heuristics=cfg.heuristics,
        has_local_clone=True,
    )
    assert breakdown.tier == TriageTier.T0


def test_assign_triage_tier_2_team_affinity():
    cfg = Config()
    pr = make_pr(
        number=4,
        requested_reviewers=[ReviewerRequest(login_or_slug="core-team", is_team=True)],
        files=[PullRequestFile(path="auth.py", additions=20, deletions=5, change_type="MODIFIED")],
    )
    touch_scores = [PathTouchScore(path="auth.py", touches_recent_90d=2)]
    breakdown = assign_triage_tier(
        pr=pr,
        touch_scores=touch_scores,
        current_username="octocat",
        heuristics=cfg.heuristics,
        has_local_clone=True,
    )
    assert breakdown.tier == TriageTier.T2
    assert "touched 1/1 files" in breakdown.reasons


def test_assign_triage_tier_3_fallback():
    cfg = Config()
    pr = make_pr(
        number=5,
        requested_reviewers=[ReviewerRequest(login_or_slug="unknown-team", is_team=True)],
    )
    breakdown = assign_triage_tier(
        pr=pr,
        touch_scores=[],
        current_username="octocat",
        heuristics=cfg.heuristics,
        has_local_clone=True,
    )
    assert breakdown.tier == TriageTier.T3


def test_assign_triage_tier_hot_team_broadcast():
    cfg = Config()
    cfg.heuristics.hot_window_hours = 6
    now = datetime.now(timezone.utc)
    hot_pushed = (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    pr = make_pr(
        number=6,
        pushed_at=hot_pushed,
        requested_reviewers=[ReviewerRequest(login_or_slug="core-team", is_team=True)],
    )
    breakdown = assign_triage_tier(
        pr=pr,
        touch_scores=[],
        current_username="octocat",
        heuristics=cfg.heuristics,
        has_local_clone=True,
    )
    assert breakdown.tier == TriageTier.T1
    assert "author pushed recently" in breakdown.reasons


def test_assign_triage_tier_not_hot():
    cfg = Config()
    cfg.heuristics.hot_window_hours = 6
    old_pushed = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    pr = make_pr(
        number=7,
        pushed_at=old_pushed,
        requested_reviewers=[ReviewerRequest(login_or_slug="core-team", is_team=True)],
    )
    breakdown = assign_triage_tier(
        pr=pr,
        touch_scores=[],
        current_username="octocat",
        heuristics=cfg.heuristics,
        has_local_clone=True,
    )
    assert breakdown.tier == TriageTier.T3


def test_process_sort_actionable_first_then_tier_then_heat():
    cfg = Config()
    cfg.github.user = "octocat"
    cfg.heuristics.hot_window_hours = 6
    repo_locator = RepoLocator(cfg.repositories)

    non_actionable = make_pr(number=100, is_draft=True)
    tier0 = make_pr(
        id="PR_T0",
        number=1,
        pushed_at="2026-08-15T09:00:00Z",
        requested_reviewers=[ReviewerRequest(login_or_slug="octocat", is_team=False)],
    )
    tier1_hot = make_pr(
        id="PR_T1",
        number=2,
        pushed_at="2026-08-15T12:00:00Z",
        requested_reviewers=[
            ReviewerRequest(login_or_slug="octocat", is_team=False),
            ReviewerRequest(login_or_slug="bob", is_team=False),
        ],
    )

    pipeline = RelevancePipeline(cfg, repo_locator)
    scored = pipeline.process([non_actionable, tier1_hot, tier0])

    assert [p.pr.number for p in scored] == [1, 2, 100]
    assert [p.score.tier for p in scored if p.is_actionable] == [TriageTier.T0, TriageTier.T1]


def test_pipeline_deterministic_tiebreak():
    cfg = Config()
    repo_locator = RepoLocator(cfg.repositories)

    same_tier = []
    for i in range(2):
        same_tier.append(make_pr(id=f"PR_{i}", number=i, repo_name_with_owner="org/repo"))
    pipeline = RelevancePipeline(cfg, repo_locator)
    scored = pipeline.process(same_tier)
    assert len([r for r in scored if r.is_actionable]) == 2