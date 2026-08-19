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
    TriageTier,
    assign_triage_tier,
    derive_followup_state,
    staleness_anchor_dt,
    wait_age_hours,
)
from gitkeeper.scoring.gates import is_actionable

WAITING_LABELS = {
    FollowUpState.WAITING_AUTHOR: "waiting on author",
    FollowUpState.WAITING_OTHERS: "waiting on others",
}


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


def _waiting_label(
    pr: PullRequestData, username: Optional[str], state: FollowUpState
) -> str:
    if state == FollowUpState.WAITING_AUTHOR:
        return "waiting on author"
    if username and pr.author.lower() == username.lower():
        return "awaiting reviewers"
    return "approved"


def queue_sort_key(item: ScoredPullRequest):
    """Band-first deterministic ordering.

    Active (ball-on-user) items first, sorted by tier then heat then size;
    waiting-band items afterwards sorted by how long the user's own last act
    has been unhonored (oldest first); non-actionable items last.
    """
    score = item.score
    active = item.is_actionable and score.follow_state == FollowUpState.ME_ACTIVE
    waiting = item.is_actionable and not active

    if active:
        return (
            0,
            score.tier,
            _push_age_hours(item.pr),
            (item.pr.additions + item.pr.deletions),
            item.pr.repo_name_with_owner,
            item.pr.number,
            "",
        )
    if waiting:
        wait_age = score.wait_age_hours if score.wait_age_hours is not None else float("inf")
        return (
            1,
            -wait_age,
            0,
            0,
            item.pr.repo_name_with_owner,
            item.pr.number,
            "",
        )
    return (
        2,
        TriageTier.T3,
        float("inf"),
        0,
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

        followup = self.config.followup

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

            # 2. Follow-up turn state
            state = derive_followup_state(pr, username)

            hidden_by_config = (
                state == FollowUpState.WAITING_AUTHOR
                and not followup.show_waiting_on_author
            ) or (
                state == FollowUpState.WAITING_OTHERS
                and not followup.show_waiting_on_others
            )
            if hidden_by_config:
                label = WAITING_LABELS.get(state, "waiting")
                results.append(
                    ScoredPullRequest(
                        pr=pr,
                        score=ScoreBreakdown(follow_state=state),
                        is_actionable=False,
                        drop_reason=f"waiting band hidden ({label})",
                    )
                )
                continue

            # 3. Local Git Context Inspection
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

            # 4. Assign triage tier only for ball-on-user items; waiting-band
            #    items carry no tier, just their waiting label and recency.
            score_breakdown = ScoreBreakdown()
            if state == FollowUpState.ME_ACTIVE:
                score_breakdown = assign_triage_tier(
                    pr=pr,
                    touch_scores=touch_scores,
                    current_username=username,
                    heuristics=self.config.heuristics,
                    has_local_clone=has_clone,
                )
            score_breakdown.follow_state = state

            # 5. Waiting / staleness overlays
            if state == FollowUpState.ME_ACTIVE:
                anchor = staleness_anchor_dt(pr, username, state)
                if anchor is not None:
                    days = (datetime.now(timezone.utc) - anchor).total_seconds() / 86400.0
                    if days > followup.staleness_warn_after_days:
                        score_breakdown.stale_days = int(days)
            else:
                score_breakdown.wait_age_hours = wait_age_hours(pr, username)
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

        # Sort actionable PRs first (priority tier, then heat, size, and a
        # deterministic tie-break), then the waiting band, with non-actionable
        # PRs at the tail.
        results.sort(key=queue_sort_key)
        return results