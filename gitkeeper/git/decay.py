from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class PathTouchScore:
    path: str
    touches_recent_90d: int = 0
    touches_90_180d: int = 0
    touches_older: int = 0
    latest_touch_timestamp: Optional[int] = None

    @property
    def total_touches(self) -> int:
        return self.touches_recent_90d + self.touches_90_180d + self.touches_older


def compute_decay_score_for_touches(
    touch_scores: List[PathTouchScore],
    max_affinity_points: float = 50.0,
) -> float:
    """
    Compute affinity points (0 - max_affinity_points) from touch history.
    - Each file with touches in <90d contributes +10 pts
    - Each file with touches in 90-180d contributes +5 pts
    - Normalized/capped at max_affinity_points.
    """
    if not touch_scores:
        return 0.0

    raw_points = 0.0
    for ts in touch_scores:
        if ts.touches_recent_90d > 0:
            raw_points += 10.0
        elif ts.touches_90_180d > 0:
            raw_points += 5.0
        elif ts.touches_older > 0:
            raw_points += 2.0

    return min(max_affinity_points, raw_points)
