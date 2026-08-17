import os
import subprocess
from pathlib import Path
import pytest
from gitkeeper.git.decay import PathTouchScore, compute_decay_score_for_touches
from gitkeeper.git.inspector import inspect_path_touches


def test_decay_score_calculation():
    scores = [
        PathTouchScore(path="a.py", touches_recent_90d=2),
        PathTouchScore(path="b.py", touches_90_180d=1),
        PathTouchScore(path="c.py", touches_older=3),
    ]
    # a.py = 10, b.py = 5, c.py = 2 -> total = 17
    assert compute_decay_score_for_touches(scores) == 17.0

    # Max points cap
    many_scores = [PathTouchScore(path=f"f{i}.py", touches_recent_90d=1) for i in range(10)]
    assert compute_decay_score_for_touches(many_scores, max_affinity_points=50.0) == 50.0


def test_git_inspector_with_real_repo(tmp_path):
    repo_dir = tmp_path / "test-repo"
    repo_dir.mkdir()
    git_base = [
        "git",
        "-C",
        str(repo_dir),
        "-c",
        "user.name=Alice Test",
        "-c",
        "user.email=alice@example.com",
        "-c",
        "commit.gpgsign=false",
    ]

    subprocess.run([*git_base, "init", "-b", "main"], check=True, capture_output=True)

    file_a = repo_dir / "service.py"
    file_a.write_text("print('hello')\n")
    subprocess.run([*git_base, "add", "service.py"], check=True, capture_output=True)
    subprocess.run([*git_base, "commit", "-m", "Initial commit"], check=True, capture_output=True)

    # Inspect touches for Alice
    touches = inspect_path_touches(
        repo_dir=repo_dir,
        paths=["service.py", "missing.py"],
        author_identifiers=["alice@example.com", "Alice Test"],
        lookback_days=180,
    )
    assert touches["service.py"].touches_recent_90d >= 1
    assert touches["service.py"].total_touches >= 1
    assert touches["missing.py"].total_touches == 0

    # Missing repo fallback
    missing_touches = inspect_path_touches(
        repo_dir=tmp_path / "non_existent",
        paths=["service.py"],
        author_identifiers=["alice@example.com"],
    )
    assert missing_touches["service.py"].total_touches == 0
