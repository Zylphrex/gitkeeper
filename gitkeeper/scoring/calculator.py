from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from typing import List, Optional
from gitkeeper.config import HeuristicsConfig
from gitkeeper.git.decay import PathTouchScore, compute_decay_score_for_touches
from gitkeeper.github.client import PullRequestData

VERDICT_STATES = {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}


class TriageTier(IntEnum):
    """Priority tiers, ascending: T0 is the highest urgency."""

    T0 = 0
    T1 = 1
    T2 = 2
    T3 = 3


class FollowUpState(IntEnum):
    """Whose turn it is on a pull request.

    Ascending only for stable storage: ME_ACTIVE sorts into the active band,
    the two waiting states into the always-visible waiting band.
    """

    ME_ACTIVE = 0
    WAITING_AUTHOR = 1
    WAITING_OTHERS = 2


@dataclass
class ScoreBreakdown:
    tier: TriageTier = TriageTier.T3
    affinity_points: float = 0.0
    rationale: str = ""
    reasons: List[str] = field(default_factory=list)
    follow_state: FollowUpState = FollowUpState.ME_ACTIVE
    stale_days: Optional[int] = None
    wait_age_hours: Optional[float] = None
    waiting_label: Optional[str] = None


def _parse_dt(iso: Optional[str]) -> Optional[datetime]:
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return None


def _is_direct_request(pr: PullRequestData, current_username: Optional[str]) -> bool:
    if not current_username:
        return False
    username = current_username.lower()
    return any(
        not req.is_team and req.login_or_slug.lower() == username
        for req in pr.requested_reviewers
    )


def _has_team_request(pr: PullRequestData) -> bool:
    return any(req.is_team for req in pr.requested_reviewers)


def _verdict_authors(pr: PullRequestData) -> set:
    return {r.author.lower() for r in pr.reviews if r.state in VERDICT_STATES}


def _is_bottleneck(pr: PullRequestData, current_username: Optional[str]) -> bool:
    """User is the last direct-requested reviewer without a verdict (or the only one asked).

    Team-alias requests are broadcast to a pool, so they don't block on one
    person and are skipped when deciding whether the user is the bottleneck.
    """
    if not _is_direct_request(pr, current_username):
        return False
    username = (current_username or "").lower()
    verdict_authors = _verdict_authors(pr)
    for req in pr.requested_reviewers:
        if req.is_team:
            continue
        if req.login_or_slug.lower() == username:
            continue
        if req.login_or_slug.lower() not in verdict_authors:
            return False
    return True


def _is_hot(pr: PullRequestData, heuristics: HeuristicsConfig) -> bool:
    if not pr.pushed_at:
        return False
    pushed_dt = _parse_dt(pr.pushed_at)
    if pushed_dt is None:
        return False
    age_hours = (datetime.now(timezone.utc) - pushed_dt).total_seconds() / 3600.0
    return age_hours <= heuristics.hot_window_hours


def _re_review_due(pr: PullRequestData, current_username: Optional[str]) -> bool:
    if not current_username or not pr.pushed_at:
        return False
    pushed_dt = _parse_dt(pr.pushed_at)
    if pushed_dt is None:
        return False
    username = current_username.lower()
    latest_mine = None
    for r in pr.reviews:
        if r.author.lower() != username:
            continue
        submitted = _parse_dt(r.submitted_at)
        if submitted is not None and (latest_mine is None or submitted > latest_mine):
            latest_mine = submitted
    return latest_mine is not None and pushed_dt > latest_mine


def _latest_my_review_dt(pr: PullRequestData, current_username: Optional[str]) -> Optional[datetime]:
    """Latest review submitted by the current user, any review state."""
    if not current_username:
        return None
    username = current_username.lower()
    latest: Optional[datetime] = None
    for r in pr.reviews:
        if r.author.lower() != username:
            continue
        submitted = _parse_dt(r.submitted_at)
        if submitted is not None and (latest is None or submitted > latest):
            latest = submitted
    return latest


def _latest_external_verdict_dt(
    pr: PullRequestData, current_username: Optional[str]
) -> Optional[datetime]:
    """Latest verdict (approve/request-changes/dismiss) from anyone but the user."""
    if not current_username:
        return None
    username = current_username.lower()
    latest: Optional[datetime] = None
    for r in pr.reviews:
        if r.author.lower() == username or r.state not in VERDICT_STATES:
            continue
        submitted = _parse_dt(r.submitted_at)
        if submitted is not None and (latest is None or submitted > latest):
            latest = submitted
    return latest


def _is_author(pr: PullRequestData, current_username: Optional[str]) -> bool:
    return bool(current_username and pr.author.lower() == current_username.lower())


def derive_followup_state(
    pr: PullRequestData, current_username: Optional[str]
) -> FollowUpState:
    """Compute whose turn a pull request rests on.

    Stateless: derived from the fetched review requests, review records,
    authorship, and latest author push time.
    """
    if _is_author(pr, current_username):
        pushed = _parse_dt(pr.pushed_at)
        external = _latest_external_verdict_dt(pr, current_username)
        if external is not None and (pushed is None or external > pushed):
            return FollowUpState.ME_ACTIVE  # respond to review on my PR
        return FollowUpState.WAITING_OTHERS  # awaiting reviewers / CI / merge

    my_verdict = _latest_my_review_dt(pr, current_username)
    if my_verdict is None:
        if _is_direct_request(pr, current_username) or _has_team_request(pr):
            return FollowUpState.ME_ACTIVE  # review due
        return FollowUpState.WAITING_OTHERS

    pushed = _parse_dt(pr.pushed_at)
    if pushed is not None and pushed > my_verdict:
        return FollowUpState.ME_ACTIVE  # re-review due

    if _latest_my_verdict(pr, current_username) == "CHANGES_REQUESTED":
        return FollowUpState.WAITING_AUTHOR
    return FollowUpState.WAITING_OTHERS


def _latest_my_verdict(
    pr: PullRequestData, current_username: Optional[str]
) -> Optional[str]:
    """State of the user's most recent submitted verdict, if any."""
    if not current_username:
        return None
    username = current_username.lower()
    latest: Optional[datetime] = None
    state: Optional[str] = None
    for r in pr.reviews:
        if r.author.lower() != username or r.state not in VERDICT_STATES:
            continue
        submitted = _parse_dt(r.submitted_at)
        if submitted is not None and (latest is None or submitted > latest):
            latest = submitted
            state = r.state
    return state


def staleness_anchor_dt(
    pr: PullRequestData,
    current_username: Optional[str],
    state: FollowUpState,
) -> Optional[datetime]:
    """Timestamp from which an active-band follow-up has been waiting on the user."""
    if state != FollowUpState.ME_ACTIVE or not current_username:
        return None

    pushed = _parse_dt(pr.pushed_at)
    my_act = _latest_my_review_dt(pr, current_username)

    if _is_author(pr, current_username) and _latest_external_verdict_dt(pr, current_username):
        return pushed or _parse_dt(pr.created_at)

    if my_act is not None and pushed is not None and pushed > my_act:
        return pushed  # re-review outstanding: author acted after me

    # Plain review-request case: GitHub's GraphQL schema exposes no timestamp
    # on a ReviewRequest, so the PR creation time is the staleness clock.
    created = _parse_dt(pr.created_at) if pr.created_at else None
    if created is not None:
        return created
    return None


def wait_age_hours(pr: PullRequestData, current_username: Optional[str]) -> Optional[float]:
    """How many hours since the user's most recent act on a waiting pull request."""
    anchors = []
    my_review = _latest_my_review_dt(pr, current_username)
    if my_review is not None:
        anchors.append(my_review)
    if _is_author(pr, current_username):
        pushed = _parse_dt(pr.pushed_at)
        if pushed is not None:
            anchors.append(pushed)
    if not anchors:
        return None
    latest = max(anchors)
    return max(0.0, (datetime.now(timezone.utc) - latest).total_seconds() / 3600.0)


def assign_triage_tier(
    pr: PullRequestData,
    touch_scores: List[PathTouchScore],
    current_username: Optional[str],
    heuristics: HeuristicsConfig,
    has_local_clone: bool = True,
) -> ScoreBreakdown:
    """
    Assign a triage tier and the reason chips that justify it.

    First match wins, which keeps a direct request structurally above a team
    ask: T0 (bottleneck) > T1 (waiting, hot, re-review) > T2 (team affinity)
    > T3 (everything else actionable).
    """
    breakdown = ScoreBreakdown()

    touched_files = sum(1 for ts in touch_scores if ts.total_touches > 0)
    if has_local_clone and touch_scores:
        breakdown.affinity_points = compute_decay_score_for_touches(
            touch_scores, max_affinity_points=50.0
        )
    elif not has_local_clone:
        breakdown.affinity_points = 15.0

    ci_ok = pr.ci_status not in ("FAILURE", "ERROR")
    directly_requested = _is_direct_request(pr, current_username)
    hot = _is_hot(pr, heuristics)
    re_review_due = _re_review_due(pr, current_username)
    respond_to_review = False
    if _is_author(pr, current_username):
        pushed = _parse_dt(pr.pushed_at)
        external = _latest_external_verdict_dt(pr, current_username)
        respond_to_review = external is not None and (pushed is None or external > pushed)

    if directly_requested and ci_ok and _is_bottleneck(pr, current_username):
        breakdown.tier = TriageTier.T0
        breakdown.reasons.append("you're the bottleneck")
    elif directly_requested or hot or re_review_due or respond_to_review:
        breakdown.tier = TriageTier.T1
        if directly_requested:
            breakdown.reasons.append("directly requested")
        if hot:
            breakdown.reasons.append("author pushed recently")
        if re_review_due:
            breakdown.reasons.append("re-review due")
        if respond_to_review:
            breakdown.reasons.append("respond to review")
    elif _has_team_request(pr) and touched_files >= heuristics.min_affinity_files:
        breakdown.tier = TriageTier.T2
        breakdown.reasons.append(f"touched {touched_files}/{len(pr.files)} files")
    else:
        breakdown.tier = TriageTier.T3
        breakdown.reasons.append("actionable")

    breakdown.rationale = ", ".join(breakdown.reasons) if breakdown.reasons else "Any review"
    return breakdown