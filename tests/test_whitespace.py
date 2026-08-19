import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from gitkeeper.diff.parser import UnifiedDiffParser
from gitkeeper.diff.whitespace import hide_whitespace

pytestmark = pytest.mark.skipif(
    shutil.which("git") is None,
    reason="git CLI is required for the oracle comparison",
)


def _make_repo(files_before: dict, files_after: dict) -> str:
    tmp = tempfile.mkdtemp(prefix="gitkeeper-gitdiff-")
    repo = Path(tmp) / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, capture_output=True, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=repo, capture_output=True, check=True
    )
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"], cwd=repo, capture_output=True, check=True
    )
    for name, content in files_before.items():
        (repo / name).write_text(content)
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "before"], cwd=repo, capture_output=True, check=True)
    for name, content in files_after.items():
        (repo / name).write_text(content)
    return str(repo)


def _git_diff(repo: str, *flags: str) -> str:
    result = subprocess.run(
        ["git", "diff", *flags],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _rows(parsed):
    """Flatten parsed file diffs to (origin, old_no, new_no) rows, dropping header rows."""
    rows = []
    for file_diff in parsed:
        for hunk in file_diff.hunks:
            for line in hunk.lines:
                if line.origin == "@":
                    continue
                rows.append((line.origin, line.old_line_no, line.new_line_no))
    return rows


def test_oracle_trailing_whitespace_and_indent_match_git_w():
    repo = _make_repo(
        {
            "a.py": "def foo():\n    return 1   \n\n\ndef bar():\n    return 2\n",
            "b.py": "x = 1\n",
        },
        {"a.py": "def foo():\n    return 1\n\n\ndef bar():\n  return 2\n", "b.py": "x = 1\n"},
    )
    plain = _git_diff(repo)
    git_w = _git_diff(repo, "-w")

    ours = hide_whitespace(UnifiedDiffParser.parse(plain))
    expected = UnifiedDiffParser.parse(git_w)

    assert _rows(ours) == _rows(expected)


def test_oracle_matches_git_w_on_interleaved_change():
    repo = _make_repo(
        {"a.py": "def verify():\n    return False\n    old_secret = SECRET\n    return True\n"},
        {"a.py": "def verify():\n  return False\n    new_secret = NEW_SECRET\n    return True\n"},
    )
    plain = _git_diff(repo)
    git_w = _git_diff(repo, "-w")

    ours = hide_whitespace(UnifiedDiffParser.parse(plain))
    expected = UnifiedDiffParser.parse(git_w)

    assert _rows(ours) == _rows(expected)