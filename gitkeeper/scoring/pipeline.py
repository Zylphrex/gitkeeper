from dataclasses import dataclass
from typing import List, Optional
from gitkeeper.config import Config
from gitkeeper.git.inspector import inspect_path_touches
from gitkeeper.github.client import PullRequestData
from gitkeeper.repos import RepoLocator
from gitkeeper.scoring.calculator import ScoreBreakdown, calculate_relevance_score
from gitkeeper.scoring.gates import is_actionable


@dataclass
class ScoredPullRequest:
    pr: PullRequestData
    score: ScoreBreakdown
    is_actionable: bool
    drop_reason: Optional[str] = None


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

            # 3. Calculate Score Breakdown
            score_breakdown = calculate_relevance_score(
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

        # Sort actionable PRs highest score first, then non-actionable
        results.sort(key=lambda item: (item.is_actionable, item.score.total_score), reverse=True)
        return results
