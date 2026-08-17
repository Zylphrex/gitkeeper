from datetime import datetime, timezone
from pathlib import Path
import subprocess
from typing import Dict, List, Optional
from gitkeeper.git.decay import PathTouchScore


def inspect_path_touches(
    repo_dir: Path,
    paths: List[str],
    author_identifiers: List[str],
    lookback_days: int = 180,
) -> Dict[str, PathTouchScore]:
    """
    Inspect local git log for given file paths, counting commits by matching authors within lookback window.
    """
    results: Dict[str, PathTouchScore] = {p: PathTouchScore(path=p) for p in paths}
    if not repo_dir.is_dir() or not (repo_dir / ".git").exists() or not paths or not author_identifiers:
        return results

    now_ts = int(datetime.now(timezone.utc).timestamp())
    cutoff_90d = now_ts - (90 * 86400)
    cutoff_180d = now_ts - (lookback_days * 86400)

    # Format: %ct = committer date timestamp, %H = commit hash, %an = author name, %ae = author email
    # Query git log for each path or all paths
    for path in paths:
        # Check if file existed/exists in git
        cmd = [
            "git",
            "-C",
            str(repo_dir),
            "log",
            f"--since={lookback_days} days ago",
            "--format=%ct",
        ]
        for author in author_identifiers:
            cmd.append(f"--author={author}")
        cmd.extend(["--", path])

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            if res.returncode == 0 and res.stdout.strip():
                timestamps = [int(ts.strip()) for ts in res.stdout.strip().split("\n") if ts.strip().isdigit()]
                score = results[path]
                for ts in timestamps:
                    if score.latest_touch_timestamp is None or ts > score.latest_touch_timestamp:
                        score.latest_touch_timestamp = ts

                    if ts >= cutoff_90d:
                        score.touches_recent_90d += 1
                    elif ts >= cutoff_180d:
                        score.touches_90_180d += 1
                    else:
                        score.touches_older += 1
        except Exception:
            continue

    return results
