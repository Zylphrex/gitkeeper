from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
from gitkeeper.config import HeuristicsConfig
from gitkeeper.git.decay import PathTouchScore, compute_decay_score_for_touches
from gitkeeper.github.client import PullRequestData


@dataclass
class ScoreBreakdown:
    affinity_points: float = 0.0
    assignment_points: float = 0.0
    urgency_points: float = 0.0
    total_score: int = 0
    rationale: str = ""
    reasons: List[str] = field(default_factory=list)


def calculate_relevance_score(
    pr: PullRequestData,
    touch_scores: List[PathTouchScore],
    current_username: Optional[str],
    heuristics: HeuristicsConfig,
    has_local_clone: bool = True,
) -> ScoreBreakdown:
    """
    Calculate composite relevance score (0 - 100) and rationale.
    """
    breakdown = ScoreBreakdown()
    reasons: List[str] = []

    # 1. Affinity Score (0 - 50 pts)
    if has_local_clone and touch_scores:
        affinity = compute_decay_score_for_touches(touch_scores, max_affinity_points=50.0)
        breakdown.affinity_points = affinity
        touched_files_count = sum(1 for ts in touch_scores if ts.total_touches > 0)
        if touched_files_count > 0:
            reasons.append(f"touched {touched_files_count}/{len(pr.files)} files")
    elif not has_local_clone:
        # Neutral fallback for uninspected repositories
        breakdown.affinity_points = 15.0
        reasons.append("no local clone")

    # 2. Assignment Points (0 - 35 pts)
    # Direct review request: +30 pts, Team alias: +10 pts
    is_direct = False
    if current_username:
        for req in pr.requested_reviewers:
            if not req.is_team and req.login_or_slug.lower() == current_username.lower():
                is_direct = True
                break

    if is_direct:
        breakdown.assignment_points = 30.0
        reasons.insert(0, "Direct review")
    else:
        breakdown.assignment_points = 10.0
        reasons.insert(0, "Team review")

    # 3. Urgency and Size Modifiers (0 - 15 pts)
    # Small diff (< 100 lines total): +10 pts
    total_lines_changed = pr.additions + pr.deletions
    if total_lines_changed < 100:
        breakdown.urgency_points += 10.0
        reasons.append(f"small PR ({total_lines_changed} lines)")

    # Waiting > 24h: +5 pts
    try:
        # ISO format: 2026-08-15T10:00:00Z
        created_dt = datetime.fromisoformat(pr.created_at.replace("Z", "+00:00"))
        now_dt = datetime.now(timezone.utc)
        age_hours = (now_dt - created_dt).total_seconds() / 3600.0
        if age_hours >= 24.0:
            breakdown.urgency_points += 5.0
            reasons.append(f"open {int(age_hours // 24)}d")
    except Exception:
        pass

    raw_total = breakdown.affinity_points + breakdown.assignment_points + breakdown.urgency_points
    breakdown.total_score = min(100, max(0, int(round(raw_total))))
    breakdown.reasons = reasons
    breakdown.rationale = ", ".join(reasons) if reasons else "Pending review"

    return breakdown
