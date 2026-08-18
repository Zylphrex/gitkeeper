from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional
from gitkeeper.config import Config
from gitkeeper.github.client import PullRequestData
from gitkeeper.git.inspector import inspect_path_touches
from gitkeeper.repos import RepoLocator
from gitkeeper.scoring.calculator import (
    ScoreBreakdown,
    TriageTier,
    assign_triage_tier,
)
from gitkeeper.scoring.gates import is_actionable


@dataclass
class ScoredPullRequest:
    pr: PullRequestData
    score: ScoreBreakdown
    is_actionable: bool
    drop_reason: Optional[str] = None


def _push_age_hours(pr: PullRequestData) -> float:
    try:
        pushed = datetime.fromisoformat(pr.pushed_at.replace("Z", "+00:00"))
        return max(0.0, (datetime.now(timezone.utc) - pushed).total_seconds() / 3600.0)
    except (ValueError, AttributeError):
        return float("inf")


def queue_sort_key(item: ScoredPullRequest) -> tuple:
    """Deterministic ordering: actionable first, then tier, heat, size, repo, number."""
    return (
        not item.is_actionable,
        item.score.tier if item.is_actionable else TriageTier.T3,
        _push_age_hours(item.pr) if item.is_actionable else float("inf"),
        (item.pr.additions + item.pr.deletions) if item.is_actionable else 0,
        item.pr.repo_name_with_owner if item.is_actionable else "",
        item.pr.number if item.is_actionable else 0,
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
            # 1. Actionability Gate
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

            # 2. Local Git Context Inspection
            repo_path = self.repo_locator.resolve(pr.repo_name_with_owner)
            has_clone = repo_path is not None
            paths = [f.path for f in pr.files]

            touch_scores_dict = {}
            if has_clone and repo_path:
                touch_scores_dict = inspect_path_touches(
                    repo_dir=repo_path,
                    paths=paths,
                    author_identifiers=author_ids,
                    lookback_days=self.config.heuristics.lookback_days,
                )

            touch_scores = list(touch_scores_dict.values())

            # 3. Assign Triage Tier
            score_breakdown = assign_triage_tier(
                pr=pr,
                touch_scores=touch_scores,
                current_username=username,
                heuristics=self.config.heuristics,
                has_local_clone=has_clone,
            )

            results.append(
                ScoredPullRequest(
                    pr=pr,
                    score=score_breakdown,
                    is_actionable=True,
                    drop_reason=None,
                )
            )

        # Sort actionable PRs first (priority tier, then heat, size, and a
        # deterministic tie-break), with non-actionable PRs at the tail.
        results.sort(key=queue_sort_key)
        return results