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

    A reviewed pull request is NOT dropped here: its turn state is derived
    later by the follow-up classifier, which routes it to the active band
    (re-review) or the waiting band (waiting on author / others).
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

    return True, None