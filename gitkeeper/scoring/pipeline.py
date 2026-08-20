from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
from gitkeeper.config import Config
from gitkeeper.github.client import PullRequestData
from gitkeeper.git.inspector import inspect_path_touches
from gitkeeper.repos import RepoLocator
from gitkeeper.scoring.calculator import (
    FollowUpState,
    ScoreBreakdown,
    derive_action_reasons,
    derive_followup_state,
)
from gitkeeper.scoring.gates import is_actionable


@dataclass
class ScoredPullRequest:
    pr: PullRequestData
    score: ScoreBreakdown
    is_actionable: bool
    drop_reason: Optional[str] = None


def _waiting_label(
    pr: PullRequestData, username: Optional[str], state: FollowUpState
) -> str:
    if state == FollowUpState.WAITING_AUTHOR:
        return "waiting on author"
    if username and pr.author.lower() == username.lower():
        return "awaiting reviewers"
    return "approved"


def _activity_timestamp(pr: PullRequestData) -> Optional[datetime]:
    """Parse the most recent activity timestamp (updated_at) for recency sorting."""
    if not pr.updated_at:
        return None
    try:
        return datetime.fromisoformat(pr.updated_at.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def activity_sort_key(item: ScoredPullRequest):
    """Order actionable PRs by most recent activity (newest first), tie-break deterministically.

    Uses GitHub's updated_at timestamp which reflects commits, comments,
    reviews, and state changes. Unparseable/empty timestamps sort oldest.
    """
    ts = _activity_timestamp(item.pr)
    if ts is None:
        ts = datetime.min.replace(tzinfo=timezone.utc)
    return (
        -ts.timestamp(),
        item.pr.repo_name_with_owner,
        item.pr.number,
        "",
    )


class RelevancePipeline:
    def __init__(self, config: Config, repo_locator: RepoLocator):
        self.config = config
        self.repo_locator = repo_locator

    def process(self, prs: List[PullRequestData]) -> List[ScoredPullRequest]:
        username = self.config.github.user
        author_ids = list(self.config.git.author_emails) + list(self.config.git.author_names)
        if username and username not in author_ids:
            author_ids.append(username)

        results: List[ScoredPullRequest] = []

        for pr in prs:
            # 1. Hard Gates (draft / closed / failing CI)
            actionable, drop_reason = is_actionable(pr, username, self.config.heuristics)
            if not actionable:
                results.append(
                    ScoredPullRequest(
                        pr=pr,
                        score=ScoreBreakdown(),
                        is_actionable=False,
                        drop_reason=drop_reason,
                    )
                )
                continue

            # 2. Follow-up turn state: whose move is it?
            state = derive_followup_state(pr, username)
            score_breakdown = ScoreBreakdown()
            score_breakdown.follow_state = state

            if state == FollowUpState.ME_ACTIVE:
                # 3. Local Git Context Inspection (overview chip only, never ranks)
                repo_path = self.repo_locator.resolve(pr.repo_name_with_owner)
                paths = [f.path for f in pr.files]
                touch_scores = []
                if repo_path is not None:
                    touch_scores_dict = inspect_path_touches(
                        repo_dir=repo_path,
                        paths=paths,
                        author_identifiers=author_ids,
                        lookback_days=self.config.heuristics.lookback_days,
                    )
                    touch_scores = list(touch_scores_dict.values())

                reasons, rationale = derive_action_reasons(
                    pr=pr,
                    touch_scores=touch_scores,
                    current_username=username,
                    heuristics=self.config.heuristics,
                )
                score_breakdown.reasons = list(reasons)
                score_breakdown.rationale = rationale
            else:
                score_breakdown.waiting_label = _waiting_label(pr, username, state)
                score_breakdown.rationale = score_breakdown.waiting_label or "waiting"

            results.append(
                ScoredPullRequest(
                    pr=pr,
                    score=score_breakdown,
                    is_actionable=True,
                    drop_reason=None,
                )
            )

        results.sort(key=activity_sort_key)
        return results