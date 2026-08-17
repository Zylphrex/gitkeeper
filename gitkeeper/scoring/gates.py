from typing import Optional
from gitkeeper.config import HeuristicsConfig
from gitkeeper.github.client import PullRequestData


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

    # 4. Already reviewed/approved by current user
    if current_username:
        user_reviews = [r for r in pr.reviews if r.author.lower() == current_username.lower()]
        for r in user_reviews:
            if r.state in ("APPROVED", "CHANGES_REQUESTED"):
                return False, f"Already submitted review: {r.state}"

    return True, None
