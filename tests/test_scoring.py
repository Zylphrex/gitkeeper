from datetime import datetime, timezone, timedelta
from gitkeeper.config import Config
from gitkeeper.git.inspector import PathTouchScore
from gitkeeper.github.client import PullRequestData, PullRequestFile, ReviewRecord, ReviewerRequest
from gitkeeper.repos import RepoLocator
from gitkeeper.scoring.calculator import (
    FollowUpState,
    ScoreBreakdown,
    derive_action_reasons,
    derive_followup_state,
    derive_viewer_status,
)
from gitkeeper.scoring.gates import is_actionable
from gitkeeper.scoring.pipeline import RelevancePipeline, ScoredPullRequest, activity_sort_key


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


# ---------- action reasons (tier-less) ----------

def _reasons(pr, touch_scores=None):
    heuristics = Config().heuristics
    reason_list, rationale = derive_action_reasons(
        pr=pr,
        touch_scores=touch_scores or [],
        current_username="octocat",
        heuristics=heuristics,
    )
    return reason_list, rationale


def test_action_reasons_directly_requested():
    pr = make_pr(
        number=1,
        requested_reviewers=[
            ReviewerRequest(login_or_slug="octocat", is_team=False),
            ReviewerRequest(login_or_slug="bob", is_team=False),
        ],
    )
    reason_list, rationale = _reasons(pr)
    assert "directly requested" in reason_list
    assert rationale


def test_action_reasons_bottleneck_when_last_unverdict():
    pr = make_pr(
        number=2,
        pushed_at="2026-08-15T09:00:00Z",
        requested_reviewers=[
            ReviewerRequest(login_or_slug="octocat", is_team=False),
            ReviewerRequest(login_or_slug="bob", is_team=False),
        ],
        reviews=[ReviewRecord(author="bob", state="APPROVED", submitted_at="2026-08-14T09:00:00Z")],
    )
    reason_list, _ = _reasons(pr)
    assert any("bottleneck" in reason for reason in reason_list)


def test_action_reasons_bottleneck_only_reviewer():
    pr = make_pr(
        number=3,
        requested_reviewers=[ReviewerRequest(login_or_slug="octocat", is_team=False)],
    )
    reason_list, _ = _reasons(pr)
    assert any("bottleneck" in reason for reason in reason_list)


def test_action_reasons_touched_files_chip():
    pr = make_pr(
        number=4,
        requested_reviewers=[ReviewerRequest(login_or_slug="core-team", is_team=True)],
        files=[PullRequestFile(path="auth.py", additions=20, deletions=5, change_type="MODIFIED")],
    )
    touch_scores = [PathTouchScore(path="auth.py", touches_recent_90d=2)]
    reason_list, _ = _reasons(pr, touch_scores)
    assert "touched 1/1 files" in reason_list


def test_action_reasons_respond_to_review_when_authored():
    pr = make_pr(
        number=21,
        author="octocat",
        pushed_at="2026-08-01T10:00:00Z",
        reviews=[ReviewRecord(author="alice", state="CHANGES_REQUESTED", submitted_at="2026-08-09T10:00:00Z")],
    )
    reason_list, _ = _reasons(pr)
    assert "respond to review" in reason_list


def test_action_reasons_no_respond_when_no_fresh_verdict():
    pr = make_pr(
        number=22,
        author="octocat",
        pushed_at="2026-08-12T10:00:00Z",
        reviews=[ReviewRecord(author="alice", state="APPROVED", submitted_at="2026-08-09T10:00:00Z")],
    )
    reason_list, _ = _reasons(pr)
    assert "respond to review" not in reason_list


def test_action_reasons_no_hot_reason_without_heat_window():
    # Heat/team-affinity tiers are gone: a team broadcast with no touched files
    # yields no reason chips beyond the fallback.
    pr = make_pr(
        number=6,
        pushed_at=(datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        requested_reviewers=[ReviewerRequest(login_or_slug="core-team", is_team=True)],
    )
    reason_list, rationale = _reasons(pr)
    assert "author pushed recently" not in reason_list
    assert rationale  # team request fallback rationale


# ---------- follow-up turn states (relevance-scoring delta) ----------

def test_followup_state_review_due():
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


# ---------- viewer action status (tui-review-client delta) ----------

def test_viewer_status_no_reviews():
    pr = make_pr(number=51)
    status = derive_viewer_status(pr, "octocat")
    assert status.has_reviewed is False
    assert status.verdict is None
    assert status.verdict_at is None
    assert status.re_review_due is False


def test_viewer_status_approved_verdict():
    pr = make_pr(
        number=52,
        reviews=[ReviewRecord(author="octocat", state="APPROVED", submitted_at="2026-08-10T10:00:00Z")],
    )
    status = derive_viewer_status(pr, "octocat")
    assert status.has_reviewed is True
    assert status.verdict == "APPROVED"
    assert status.verdict_at is not None
    assert status.verdict_at.isoformat().startswith("2026-08-10T10:00:00")
    assert status.re_review_due is False


def test_viewer_status_requested_changes_verdict():
    pr = make_pr(
        number=53,
        reviews=[ReviewRecord(author="octocat", state="CHANGES_REQUESTED", submitted_at="2026-08-09T10:00:00Z")],
    )
    status = derive_viewer_status(pr, "octocat")
    assert status.has_reviewed is True
    assert status.verdict == "CHANGES_REQUESTED"


def test_viewer_status_re_review_due_after_author_push():
    pr = make_pr(
        number=54,
        reviews=[ReviewRecord(author="octocat", state="APPROVED", submitted_at="2026-08-09T10:00:00Z")],
        pushed_at="2026-08-12T10:00:00Z",
    )
    status = derive_viewer_status(pr, "octocat")
    assert status.has_reviewed is True
    assert status.re_review_due is True


def test_viewer_status_re_review_not_due_without_new_push():
    pr = make_pr(
        number=55,
        reviews=[ReviewRecord(author="octocat", state="APPROVED", submitted_at="2026-08-12T10:00:00Z")],
        pushed_at="2026-08-09T10:00:00Z",
    )
    status = derive_viewer_status(pr, "octocat")
    assert status.re_review_due is False


def test_viewer_status_unknown_username_is_none_safe():
    pr = make_pr(
        number=56,
        reviews=[ReviewRecord(author="alice", state="APPROVED", submitted_at="2026-08-10T10:00:00Z")],
    )
    status = derive_viewer_status(pr, None)
    assert status.has_reviewed is False
    status_missing = derive_viewer_status(pr, "")
    assert status_missing.has_reviewed is False


def test_viewer_status_username_is_case_insensitive():
    pr = make_pr(
        number=57,
        reviews=[ReviewRecord(author="OctoCat", state="APPROVED", submitted_at="2026-08-10T10:00:00Z")],
    )
    status = derive_viewer_status(pr, "octocat")
    assert status.has_reviewed is True
    assert status.verdict == "APPROVED"


# ---------- activity-ordered queue (relevance-scoring delta) ----------

def _scored(number: int, **overrides) -> ScoredPullRequest:
    pr = make_pr(number=number, **overrides)
    return ScoredPullRequest(
        pr=pr,
        score=ScoreBreakdown(follow_state=FollowUpState.ME_ACTIVE),
        is_actionable=True,
    )


def test_activity_sort_key_newest_first():
    old = _scored(1, updated_at="2026-08-01T00:00:00Z")
    new = _scored(2, updated_at="2026-08-20T00:00:00Z")
    mid = _scored(3, updated_at="2026-08-10T00:00:00Z")
    items = sorted([old, new, mid], key=activity_sort_key)
    assert [i.pr.number for i in items] == [2, 3, 1]


def test_activity_sort_key_deterministic_tiebreak():
    a = _scored(1, repo_name_with_owner="a/one", updated_at="2026-08-10T00:00:00Z")
    b = _scored(2, repo_name_with_owner="z/two", updated_at="2026-08-10T00:00:00Z")
    assert activity_sort_key(a)[1:] < activity_sort_key(b)[1:]
    # same repo: number breaks the tie
    c = _scored(3, repo_name_with_owner="a/one", updated_at="2026-08-10T00:00:00Z")
    assert activity_sort_key(a)[:1] == activity_sort_key(c)[:1]
    assert activity_sort_key(a)[2] < activity_sort_key(c)[2]


def test_activity_sort_key_unparseable_sorts_oldest():
    junk = ScoredPullRequest(
        pr=make_pr(number=1, updated_at=""),
        score=ScoreBreakdown(follow_state=FollowUpState.ME_ACTIVE),
        is_actionable=True,
    )
    fresh = ScoredPullRequest(
        pr=make_pr(number=2, updated_at="2026-08-20T00:00:00Z"),
        score=ScoreBreakdown(follow_state=FollowUpState.ME_ACTIVE),
        is_actionable=True,
    )
    items = sorted([fresh, junk], key=activity_sort_key)
    assert [i.pr.number for i in items] == [2, 1]


def test_pipeline_orders_actionable_by_activity():
    cfg = Config()
    cfg.github.user = "octocat"
    repo_locator = RepoLocator(cfg.repositories)

    non_actionable = make_pr(number=100, is_draft=True)
    older = make_pr(
        number=1,
        updated_at="2026-08-10T00:00:00Z",
        requested_reviewers=[ReviewerRequest(login_or_slug="octocat", is_team=False)],
    )
    newer = make_pr(
        number=2,
        updated_at="2026-08-20T00:00:00Z",
        requested_reviewers=[
            ReviewerRequest(login_or_slug="octocat", is_team=False),
            ReviewerRequest(login_or_slug="bob", is_team=False),
        ],
    )

    pipeline = RelevancePipeline(cfg, repo_locator)
    scored = pipeline.process([non_actionable, older, newer])

    actionable = [p for p in scored if p.is_actionable]
    assert [p.pr.number for p in actionable] == [2, 1]


def test_pipeline_interleaves_waiting_and_active_by_activity():
    cfg = Config()
    cfg.github.user = "octocat"
    repo_locator = RepoLocator(cfg.repositories)

    awaiting_action = make_pr(
        number=1,
        author="alice",
        updated_at="2026-08-05T00:00:00Z",
        requested_reviewers=[ReviewerRequest(login_or_slug="octocat", is_team=False)],
    )
    waiting_others = make_pr(
        number=2,
        author="alice",
        updated_at="2026-08-20T00:00:00Z",
        requested_reviewers=[ReviewerRequest(login_or_slug="octocat", is_team=False)],
        reviews=[ReviewRecord(author="octocat", state="APPROVED", submitted_at="2026-08-02T00:00:00Z")],
    )

    pipeline = RelevancePipeline(cfg, repo_locator)
    scored = pipeline.process([awaiting_action, waiting_others])
    actionable = [p for p in scored if p.is_actionable]
    # waiting PR with newer activity appears ahead of the older awaiting-action PR
    assert [p.pr.number for p in actionable] == [2, 1]
    by_number = {p.pr.number: p for p in actionable}
    assert by_number[2].score.follow_state == FollowUpState.WAITING_OTHERS
    assert by_number[1].score.follow_state == FollowUpState.ME_ACTIVE


def test_pipeline_sets_reasons_and_waiting_labels():
    cfg = Config()
    cfg.github.user = "octocat"
    repo_locator = RepoLocator(cfg.repositories)

    active_pr = make_pr(
        number=1,
        author="alice",
        requested_reviewers=[
            ReviewerRequest(login_or_slug="octocat", is_team=False),
            ReviewerRequest(login_or_slug="bob", is_team=False),
        ],
    )
    waiting_pr = make_pr(
        number=2,
        author="alice",
        requested_reviewers=[ReviewerRequest(login_or_slug="octocat", is_team=False)],
        reviews=[ReviewRecord(author="octocat", state="CHANGES_REQUESTED", submitted_at="2026-08-09T10:00:00Z")],
    )

    pipeline = RelevancePipeline(cfg, repo_locator)
    scored = pipeline.process([waiting_pr, active_pr])
    by_number = {p.pr.number: p for p in scored}
    assert "directly requested" in by_number[1].score.reasons
    assert by_number[2].score.follow_state == FollowUpState.WAITING_AUTHOR
    assert by_number[2].score.waiting_label == "waiting on author"
