import re
from dataclasses import replace
from typing import List, Optional, Tuple

from gitkeeper.diff.parser import DiffHunk, DiffLine, FileDiff

_WS_RE = re.compile(r"\s+")


def _strip_ws(text: str) -> str:
    """Strip *all* whitespace from a line, matching `git diff --ignore-all-space`."""
    return _WS_RE.sub("", text)


def _align_rows(
    old: List[DiffLine],
    new: List[DiffLine],
) -> List[Tuple[str, int, Optional[int]]]:
    """Run an LCS alignment of *old* and *new* sequences using whitespace-insensitive equality.

    Returns a walk of rows in merged order: ``("match", old_idx, new_idx)``
    for aligned pairs, ``("old", idx, None)`` for unpaired old lines, and
    ``("new", idx, None)`` for unpaired new lines.
    """
    old_norm = [_strip_ws(line.content) for line in old]
    new_norm = [_strip_ws(line.content) for line in new]
    n, m = len(old), len(new)

    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            if old_norm[i] == new_norm[j]:
                dp[i][j] = dp[i + 1][j + 1] + 1
            else:
                dp[i][j] = dp[i + 1][j] if dp[i + 1][j] >= dp[i][j + 1] else dp[i][j + 1]

    rows: List[Tuple[str, int, Optional[int]]] = []
    i = j = 0
    while i < n and j < m:
        if _strip_ws(old[i].content) == _strip_ws(new[j].content):
            rows.append(("match", i, j))
            i += 1
            j += 1
        elif dp[i + 1][j] >= dp[i][j + 1]:
            rows.append(("old", i, None))
            i += 1
        else:
            rows.append(("new", None, j))
            j += 1
    while i < n:
        rows.append(("old", i, None))
        i += 1
    while j < m:
        rows.append(("new", None, j))
        j += 1
    return rows


def _filter_hunk(hunk: DiffHunk) -> Optional[DiffHunk]:
    """Collapse whitespace-only changes in *hunk*, or return ``None`` when all changes collapse.

    Old-side lines are the context rows plus deletions; new-side lines are the
    context rows plus additions. Lines matched by the whitespace-insensitive
    alignment become a single context row carrying both sides' line numbers.
    """
    old_side = [line for line in hunk.lines if line.old_line_no is not None]
    new_side = [line for line in hunk.lines if line.new_line_no is not None]

    emitted: List[DiffLine] = []
    for kind, old_idx, new_idx in _align_rows(old_side, new_side):
        if kind == "match":
            old_line = old_side[old_idx]
            new_line = new_side[new_idx]
            emitted.append(
                DiffLine(
                    origin=" ",
                    content=new_line.content,
                    old_line_no=old_line.old_line_no,
                    new_line_no=new_line.new_line_no,
                )
            )
        elif kind == "old":
            old_line = old_side[old_idx]
            emitted.append(
                DiffLine(
                    origin="-",
                    content=old_line.content,
                    old_line_no=old_line.old_line_no,
                    new_line_no=None,
                )
            )
        else:
            new_line = new_side[new_idx]
            emitted.append(
                DiffLine(
                    origin="+",
                    content=new_line.content,
                    old_line_no=None,
                    new_line_no=new_line.new_line_no,
                )
            )

    if not any(line.origin in ("-", "+") for line in emitted):
        return None

    return DiffHunk(
        header=hunk.header,
        old_start=hunk.old_start,
        old_count=hunk.old_count,
        new_start=hunk.new_start,
        new_count=hunk.new_count,
        lines=emitted,
    )


def hide_whitespace(file_diffs: List[FileDiff]) -> List[FileDiff]:
    """Return a new list of file diffs with whitespace-only changes collapsed.

    Whitespace-equal ``-``/``+`` pairs become shared context rows; hunks whose
    changes all collapse are dropped. Files whose hunks all drop are retained
    (with empty hunks) so the viewer can show a whitespace-only state.
    """
    result: List[FileDiff] = []
    for file_diff in file_diffs:
        hunks: List[DiffHunk] = []
        for hunk in file_diff.hunks:
            filtered = _filter_hunk(hunk)
            if filtered is not None:
                hunks.append(filtered)
        result.append(replace(file_diff, hunks=hunks))
    return result