from datetime import datetime
from typing import Optional
from gitkeeper.config import HeuristicsConfig
from gitkeeper.github.client import PullRequestData


def _parse_dt(iso: Optional[str]) -> Optional[datetime]:
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return None


def _latest_my_review_dt(pr: PullRequestData, username: str) -> Optional[datetime]:
    latest = None
    for r in pr.reviews:
        if r.author.lower() != username.lower():
            continue
        submitted = _parse_dt(r.submitted_at)
        if submitted is not None and (latest is None or submitted > latest):
            latest = submitted
    return latest


def is_actionable(
    pr: PullRequestData,
    current_username: Optional[str],
    heuristics: HeuristicsConfig,
) -> tuple[bool, Optional[str]]:
    """
    Check if a pull request passes actionability hard gates.
    Returns (is_actionable, drop_reason).
    """
    # 1. Draft gate
    if heuristics.ignore_drafts and pr.is_draft:
        return False, "PR is a draft"

    # 2. State gate
    if pr.state != "OPEN":
        return False, f"PR is {pr.state.lower()}"

    # 3. Failing CI gate
    if heuristics.ignore_failing_ci and pr.ci_status in ("FAILURE", "ERROR"):
        return False, "CI status is failing/error"

    # 4. Already reviewed/approved by current user, unless the author pushed
    #    new commits after the user's last verdict (a re-review is due).
    if current_username:
        user_reviews = [r for r in pr.reviews if r.author.lower() == current_username.lower()]
        verdict_reviews = [r for r in user_reviews if r.state in ("APPROVED", "CHANGES_REQUESTED")]
        for r in verdict_reviews:
            latest_mine = _latest_my_review_dt(pr, current_username)
            pushed_dt = _parse_dt(pr.pushed_at)
            if pushed_dt is not None and latest_mine is not None and pushed_dt > latest_mine:
                return True, "re-review"
            return False, f"Already submitted review: {r.state}"

    return True, None