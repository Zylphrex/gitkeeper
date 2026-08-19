import pytest
from datetime import datetime, timezone, timedelta
from gitkeeper.config import Config
from gitkeeper.git.decay import PathTouchScore
from gitkeeper.github.client import PullRequestData, PullRequestFile, ReviewRecord, ReviewerRequest
from gitkeeper.repos import RepoLocator
from gitkeeper.scoring.calculator import (
    FollowUpState,
    TriageTier,
    assign_triage_tier,
    derive_followup_state,
    staleness_anchor_dt,
)
from gitkeeper.scoring.gates import is_actionable
from gitkeeper.scoring.pipeline import RelevancePipeline, ScoredPullRequest, queue_sort_key


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

    pr_closed = make_pr(number=3, state="MERGED")
    actionable, reason = is_actionable(pr_closed, "octocat", cfg.heuristics)
    assert actionable is False
    assert "merged" in reason


def test_reviewed_prs_pass_the_gate_and_are_classified_not_dropped():
    cfg = Config()
    requested = [ReviewerRequest(login_or_slug="octocat", is_team=False)]
    stale = make_pr(
        number=4,
        requested_reviewers=requested,
        reviews=[ReviewRecord(author="octocat", state="CHANGES_REQUESTED", submitted_at="2026-08-09T10:00:00Z")],
    )
    assert is_actionable(stale, "octocat", cfg.heuristics) == (True, None)
    assert derive_followup_state(stale, "octocat") == FollowUpState.WAITING_AUTHOR

    refreshed = make_pr(
        number=5,
        requested_reviewers=requested,
        pushed_at="2026-08-12T10:00:00Z",
        reviews=[ReviewRecord(author="octocat", state="CHANGES_REQUESTED", submitted_at="2026-08-10T10:00:00Z")],
    )
    assert is_actionable(refreshed, "octocat", cfg.heuristics) == (True, None)
    assert derive_followup_state(refreshed, "octocat") == FollowUpState.ME_ACTIVE


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

# ---------- follow-up turn states (relevance-scoring delta) ----------

def test_followup_state_review_due():
    cfg = Config()
    pr = make_pr(
        number=11,
        author="alice",
        requested_reviewers=[ReviewerRequest(login_or_slug="octocat", is_team=False)],
    )
    assert derive_followup_state(pr, "octocat") == FollowUpState.ME_ACTIVE


def test_followup_state_waiting_on_author():
    pr = make_pr(
        number=12,
        author="alice",
        requested_reviewers=[ReviewerRequest(login_or_slug="octocat", is_team=False)],
        reviews=[ReviewRecord(author="octocat", state="CHANGES_REQUESTED", submitted_at="2026-08-09T10:00:00Z")],
    )
    assert derive_followup_state(pr, "octocat") == FollowUpState.WAITING_AUTHOR


def test_followup_state_re_review_after_author_push():
    pr = make_pr(
        number=13,
        author="alice",
        requested_reviewers=[ReviewerRequest(login_or_slug="octocat", is_team=False)],
        reviews=[ReviewRecord(author="octocat", state="CHANGES_REQUESTED", submitted_at="2026-08-09T10:00:00Z")],
        pushed_at="2026-08-12T10:00:00Z",
    )
    assert derive_followup_state(pr, "octocat") == FollowUpState.ME_ACTIVE


def test_followup_state_approved_idle_waits_on_others():
    pr = make_pr(
        number=14,
        author="alice",
        requested_reviewers=[ReviewerRequest(login_or_slug="octocat", is_team=False)],
        reviews=[ReviewRecord(author="octocat", state="APPROVED", submitted_at="2026-08-09T10:00:00Z")],
    )
    assert derive_followup_state(pr, "octocat") == FollowUpState.WAITING_OTHERS


def test_followup_state_authored_with_fresh_verdict_is_active():
    pr = make_pr(
        number=15,
        author="octocat",
        pushed_at="2026-08-01T10:00:00Z",
        reviews=[ReviewRecord(author="alice", state="CHANGES_REQUESTED", submitted_at="2026-08-09T10:00:00Z")],
    )
    assert derive_followup_state(pr, "octocat") == FollowUpState.ME_ACTIVE


def test_followup_state_authored_idle_waits_on_reviewers():
    pr = make_pr(number=16, author="octocat", pushed_at="2026-08-01T10:00:00Z")
    assert derive_followup_state(pr, "octocat") == FollowUpState.WAITING_OTHERS


def test_followup_state_ignores_external_verdict_before_author_push():
    pr = make_pr(
        number=17,
        author="octocat",
        pushed_at="2026-08-12T10:00:00Z",
        reviews=[ReviewRecord(author="alice", state="CHANGES_REQUESTED", submitted_at="2026-08-09T10:00:00Z")],
    )
    assert derive_followup_state(pr, "octocat") == FollowUpState.WAITING_OTHERS


# ---------- authored-response tier rule (triage-tiers delta) ----------

def test_assign_triage_tier_authored_respond_to_review():
    pr = make_pr(
        number=21,
        author="octocat",
        pushed_at="2026-08-01T10:00:00Z",
        reviews=[ReviewRecord(author="alice", state="CHANGES_REQUESTED", submitted_at="2026-08-09T10:00:00Z")],
    )
    breakdown = assign_triage_tier(
        pr=pr, touch_scores=[], current_username="octocat", heuristics=Config().heuristics
    )
    assert breakdown.tier == TriageTier.T1
    assert "respond to review" in breakdown.reasons


def test_assign_triage_tier_authored_old_feedback_is_not_t1():
    pr = make_pr(
        number=22,
        author="octocat",
        pushed_at="2026-08-12T10:00:00Z",
        reviews=[ReviewRecord(author="alice", state="APPROVED", submitted_at="2026-08-09T10:00:00Z")],
    )
    breakdown = assign_triage_tier(
        pr=pr, touch_scores=[], current_username="octocat", heuristics=Config().heuristics
    )
    assert "respond to review" not in breakdown.reasons


def test_assign_triage_tier_authored_respond_does_not_outrank_bottleneck():
    pr = make_pr(
        number=23,
        author="bob",
        pushed_at="2026-08-01T10:00:00Z",
        requested_reviewers=[
            ReviewerRequest(login_or_slug="octocat", is_team=False),
            ReviewerRequest(login_or_slug="alice", is_team=False),
        ],
        reviews=[ReviewRecord(author="alice", state="APPROVED", submitted_at="2026-08-09T10:00:00Z")],
    )
    breakdown = assign_triage_tier(
        pr=pr, touch_scores=[], current_username="octocat", heuristics=Config().heuristics
    )
    assert breakdown.tier == TriageTier.T0


# ---------- staleness marker (relevance-scoring delta) ----------

def test_staleness_anchor_uses_created_at_when_request_time_unavailable():
    from datetime import datetime, timedelta, timezone

    created = (datetime.now(timezone.utc) - timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    pr = make_pr(
        number=31,
        created_at=created,
        requested_reviewers=[ReviewerRequest(login_or_slug="octocat", is_team=False)],
    )
    anchor = staleness_anchor_dt(pr, "octocat", FollowUpState.ME_ACTIVE)
    assert anchor is not None
    days = (datetime.now(timezone.utc) - anchor).total_seconds() / 86400.0
    assert 4.5 < days < 5.5


def test_staleness_anchor_falls_back_to_created_at():
    pr = make_pr(
        number=32,
        created_at="2026-08-10T00:00:00Z",
        requested_reviewers=[ReviewerRequest(login_or_slug="octocat", is_team=False)],
    )
    anchor = staleness_anchor_dt(pr, "octocat", FollowUpState.ME_ACTIVE)
    assert anchor is not None


def test_staleness_anchor_none_for_waiting_band():
    pr = make_pr(
        number=33,
        requested_reviewers=[ReviewerRequest(login_or_slug="octocat", is_team=False)],
        reviews=[ReviewRecord(author="octocat", state="CHANGES_REQUESTED", submitted_at="2026-08-09T10:00:00Z")],
    )
    assert staleness_anchor_dt(pr, "octocat", FollowUpState.WAITING_AUTHOR) is None


def test_pipeline_marks_stale_only_past_threshold():
    from datetime import datetime, timedelta, timezone

    cfg = Config()
    cfg.github.user = "octocat"
    repo_locator = RepoLocator(cfg.repositories)

    old_created = (datetime.now(timezone.utc) - timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    fresh_created = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    stale = make_pr(
        number=34,
        created_at=old_created,
        requested_reviewers=[ReviewerRequest(login_or_slug="octocat", is_team=False)],
    )
    fresh = make_pr(
        number=35,
        created_at=fresh_created,
        requested_reviewers=[ReviewerRequest(login_or_slug="octocat", is_team=False)],
    )

    scored = RelevancePipeline(cfg, repo_locator).process([stale, fresh])
    by_number = {s.pr.number: s for s in scored}
    assert by_number[34].score.stale_days is not None
    assert by_number[35].score.stale_days is None


def test_pipeline_honours_staleness_threshold_config():
    from datetime import datetime, timedelta, timezone

    cfg = Config()
    cfg.github.user = "octocat"
    cfg.followup.staleness_warn_after_days = 10
    repo_locator = RepoLocator(cfg.repositories)

    requested = (datetime.now(timezone.utc) - timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    pr = make_pr(
        number=36,
        created_at=requested,
        requested_reviewers=[ReviewerRequest(login_or_slug="octocat", is_team=False)],
    )
    scored = RelevancePipeline(cfg, repo_locator).process([pr])
    assert scored[0].score.stale_days is None


# ---------- queue ordering (triage-tiers delta) ----------

def _make_active(number: int, **overrides) -> ScoredPullRequest:
    from gitkeeper.scoring.calculator import ScoreBreakdown

    pr = make_pr(number=number, **overrides)
    return ScoredPullRequest(pr=pr, score=ScoreBreakdown(tier=TriageTier.T3), is_actionable=True)


def test_queue_sort_active_before_waiting_before_dropped():
    from gitkeeper.scoring.calculator import ScoreBreakdown
    from gitkeeper.scoring.pipeline import ScoredPullRequest

    active = _make_active(1, requested_reviewers=[ReviewerRequest(login_or_slug="octocat", is_team=False)])
    sb_wait = ScoreBreakdown(follow_state=FollowUpState.WAITING_AUTHOR, waiting_label="waiting on author")
    waiting = ScoredPullRequest(pr=make_pr(number=2), score=sb_wait, is_actionable=True)
    dropped = ScoredPullRequest(pr=make_pr(number=3, is_draft=True), score=ScoreBreakdown(), is_actionable=False)

    items = [waiting, dropped, active]
    items.sort(key=queue_sort_key)
    assert [i.pr.number for i in items] == [1, 2, 3]


def test_queue_waiting_orders_oldest_first():
    from gitkeeper.scoring.calculator import ScoreBreakdown
    from gitkeeper.scoring.pipeline import ScoredPullRequest

    def waiting(number: int, age: float) -> ScoredPullRequest:
        sb = ScoreBreakdown(follow_state=FollowUpState.WAITING_AUTHOR, wait_age_hours=age)
        return ScoredPullRequest(pr=make_pr(number=number), score=sb, is_actionable=True)

    older = waiting(101, 120.0)
    newer = waiting(102, 24.0)
    oldest = waiting(103, 720.0)

    items = sorted([newer, older, oldest], key=queue_sort_key)
    assert [i.pr.number for i in items] == [103, 101, 102]
