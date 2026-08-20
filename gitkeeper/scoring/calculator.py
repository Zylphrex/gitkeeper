from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from typing import List, Optional
from gitkeeper.config import HeuristicsConfig
from gitkeeper.git.inspector import PathTouchScore
from gitkeeper.github.client import PullRequestData

VERDICT_STATES = {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}


class FollowUpState(IntEnum):
    """Whose turn it is on a pull request."""

    ME_ACTIVE = 0
    WAITING_AUTHOR = 1
    WAITING_OTHERS = 2


@dataclass
class ViewerStatus:
    """The current viewer's recorded actions on a pull request.

    Derived from review records already fetched from GitHub (author, state,
    submitted timestamp), not from any new data source.
    """

    has_reviewed: bool = False
    verdict: Optional[str] = None  # APPROVED / CHANGES_REQUESTED / DISMISSED
    verdict_at: Optional[datetime] = None
    re_review_due: bool = False


@dataclass
class ScoreBreakdown:
    follow_state: FollowUpState = FollowUpState.ME_ACTIVE
    rationale: str = ""
    reasons: List[str] = field(default_factory=list)
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


def derive_viewer_status(
    pr: PullRequestData, current_username: Optional[str]
) -> ViewerStatus:
    """Summarize the viewer's own recorded actions on a pull request.

    Returns ``None``-safe values on all inputs (including a missing
    username), mirroring how the band logic treats unknown viewers.
    """
    latest_mine = _latest_my_review_dt(pr, current_username)
    if latest_mine is None:
        return ViewerStatus()
    return ViewerStatus(
        has_reviewed=True,
        verdict=_latest_my_verdict(pr, current_username),
        verdict_at=latest_mine,
        re_review_due=_re_review_due(pr, current_username),
    )


def derive_action_reasons(
    pr: PullRequestData,
    touch_scores: List[PathTouchScore],
    current_username: Optional[str],
    heuristics: HeuristicsConfig,
) -> tuple[list[str], str]:
    """Produce the observable reasons a pull request is actionable, without tiers.

    Returns ``(reasons, rationale)`` where rationale joins the chips so the
    overview can show why the pull request is worth acting on.
    """
    reasons: list[str] = []

    if _is_bottleneck(pr, current_username):
        reasons.append("you're the bottleneck")
    elif _is_direct_request(pr, current_username):
        reasons.append("directly requested")
    if _re_review_due(pr, current_username):
        reasons.append("re-review due")
    if _is_author(pr, current_username):
        pushed = _parse_dt(pr.pushed_at)
        external = _latest_external_verdict_dt(pr, current_username)
        if external is not None and (pushed is None or external > pushed):
            reasons.append("respond to review")

    touched_files = sum(1 for ts in touch_scores if ts.total_touches > 0)
    if touched_files:
        reasons.append(f"touched {touched_files}/{len(pr.files)} files")

    if reasons:
        rationale = ", ".join(reasons)
    elif _has_team_request(pr):
        rationale = "team request"
    else:
        rationale = "Any review"
    return reasons, rationale