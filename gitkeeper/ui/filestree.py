from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

ELLIPSIS = "…"
CHAIN_SEPARATOR = " › "
PATH_SEPARATOR = "/"

# Usable width budget for a single #file-option-list row. The pane is 32 cols;
# subtract the border and list padding to stay safely under the wrap threshold.
ROW_WIDTH = 30
BADGE_WIDTH = 6  # "[MOD] " badge plus its trailing space
INDENT_WIDTH = 2  # spaces per tree depth level


@dataclass
class TreeHeader:
    """A non-navigable directory landmark row."""

    label: str
    depth: int


@dataclass
class TreeLeaf:
    """A selectable file row carrying its index into the source file_diffs."""

    label: str
    file_index: int
    depth: int


TreeRow = Union[TreeHeader, TreeLeaf]


@dataclass
class _DirNode:
    """One directory level in the path trie. Files terminate as indices here."""

    name: str
    subdirs: Dict[str, "_DirNode"] = field(default_factory=dict)
    files: List[int] = field(default_factory=list)


def shorten_path(
    segments: List[str],
    max_cols: int,
    sep: str = PATH_SEPARATOR,
) -> str:
    """Join *segments* with *sep*, eliding the middle behind an ellipsis.

    The last two segments (the tail) always survive; leading segments are kept
    from the tail outward while they fit in *max_cols* columns.
    """
    if not segments:
        return ""
    joined = sep.join(segments)
    if len(joined) <= max_cols:
        return joined

    anchor = sep.join(segments[-2:])
    ellipsis_piece = ELLIPSIS + sep
    core = ellipsis_piece + anchor
    if len(core) > max_cols:
        # Even the minimal display is too wide: trim the head, keep the tail.
        head_budget = max(max_cols - len(ellipsis_piece), 1)
        core = ELLIPSIS + anchor[-head_budget:]

    for segment in reversed(segments[:-2]):
        candidate = segment + sep + core
        if len(candidate) > max_cols:
            break
        core = candidate
    return core


def _insert(root_dirs: Dict[str, _DirNode], segments: List[str], file_index: int) -> None:
    node = root_dirs.setdefault(segments[0], _DirNode(segments[0]))
    for segment in segments[1:-1]:
        node = node.subdirs.setdefault(segment, _DirNode(segment))
    node.files.append(file_index)


def _leaf_name(file_diff) -> str:
    return file_diff.display_path.rsplit(PATH_SEPARATOR, 1)[-1]


def _emit(
    node: _DirNode,
    depth: int,
    file_diffs,
    rows: List[TreeRow],
    max_row_cols: int,
) -> None:
    folded: List[_DirNode] = []
    current = node
    # Fold single-child chains: while a directory has exactly one subdir and
    # no files of its own, it is absorbed into the header label.
    while len(current.subdirs) == 1 and not current.files:
        folded.append(current)
        current = next(iter(current.subdirs.values()))
    folded.append(current)
    last = current

    rows.append(
        TreeHeader(
            label=shorten_path(
                [node.name for node in folded],
                max_row_cols - INDENT_WIDTH * depth,
                sep=CHAIN_SEPARATOR,
            ),
            depth=depth,
        )
    )

    leaf_depth = depth + 1
    for file_index in sorted(last.files):
        rows.append(
            TreeLeaf(
                label=shorten_path(
                    [_leaf_name(file_diffs[file_index])],
                    max_row_cols - BADGE_WIDTH - INDENT_WIDTH * leaf_depth,
                ),
                file_index=file_index,
                depth=leaf_depth,
            )
        )
    for name in sorted(last.subdirs):
        _emit(last.subdirs[name], leaf_depth, file_diffs, rows, max_row_cols)


def build_file_tree(file_diffs, max_row_cols: int = ROW_WIDTH) -> List[TreeRow]:
    """Build compact directory-tree rows for *file_diffs*.

    Directory-only chains with a single child are flattened onto one header
    row; file rows carry the index they occupy in *file_diffs*. A single-file
    list renders without any directory headers.
    """
    if not file_diffs:
        return []

    if len(file_diffs) == 1:
        segments = file_diffs[0].display_path.strip(PATH_SEPARATOR).split(PATH_SEPARATOR)
        return [
            TreeLeaf(
                label=shorten_path(segments, max_row_cols - BADGE_WIDTH),
                file_index=0,
                depth=0,
            )
        ]

    root_dirs: Dict[str, _DirNode] = {}
    root_files: List[int] = []
    for index, file_diff in enumerate(file_diffs):
        segments = file_diff.display_path.strip(PATH_SEPARATOR).split(PATH_SEPARATOR)
        if len(segments) == 1:
            root_files.append(index)
            continue
        _insert(root_dirs, segments, index)

    rows: List[TreeRow] = []
    for index in sorted(root_files):
        file_diff = file_diffs[index]
        rows.append(
            TreeLeaf(
                label=shorten_path(
                    [file_diff.display_path],
                    max_row_cols - BADGE_WIDTH,
                ),
                file_index=index,
                depth=0,
            )
        )
    for name in sorted(root_dirs):
        _emit(root_dirs[name], 0, file_diffs, rows, max_row_cols)
    return rows