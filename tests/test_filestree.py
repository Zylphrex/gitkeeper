from gitkeeper.diff.parser import FileDiff
from gitkeeper.ui.filestree import build_file_tree, shorten_path, TreeHeader, TreeLeaf


def _file(path: str, **kwargs) -> FileDiff:
    return FileDiff(old_path=path, new_path=path, **kwargs)


def test_multi_file_tree_headers_and_leaf_order():
    files = [
        _file("a/b/one.ts"),
        _file("a/b/two.ts"),
        _file("c/three.ts"),
        _file("README.md"),
    ]
    rows = build_file_tree(files)

    expected = [
        (TreeLeaf, 3, 0, "README.md"),
        (TreeHeader, None, 0, "a › b"),
        (TreeLeaf, 0, 1, "one.ts"),
        (TreeLeaf, 1, 1, "two.ts"),
        (TreeHeader, None, 0, "c"),
        (TreeLeaf, 2, 1, "three.ts"),
    ]
    assert len(rows) == len(expected)
    for row, (kind, file_index, depth, label) in zip(rows, expected):
        assert isinstance(row, kind)
        assert row.depth == depth
        assert row.label == label
        if file_index is not None:
            assert row.file_index == file_index


def test_file_index_maps_across_interspersed_headers():
    files = [
        _file("x/nested/deep/alpha.py"),
        _file("x/root.py"),
        _file("y/other.py"),
    ]
    leaf_indices = [
        row.file_index for row in build_file_tree(files) if isinstance(row, TreeLeaf)
    ]
    # Order of emission: x/root.py (index 1), x/nested/deep/alpha.py (index 0),
    # then y/other.py (index 2) across two separate header branches.
    assert leaf_indices == [1, 0, 2]
    header_count = sum(1 for row in build_file_tree(files) if isinstance(row, TreeHeader))
    # x/ has a file of its own (header "x") plus a single-child chain
    # nested › deep (a second header); y/ is the third.
    assert header_count == 3


def test_single_file_has_no_headers_and_keeps_parent():
    files = [_file("dashboard/Billing.tsx")]
    rows = build_file_tree(files)
    assert len(rows) == 1
    row = rows[0]
    assert isinstance(row, TreeLeaf)
    assert row.file_index == 0
    assert row.depth == 0
    assert row.label.endswith("Billing.tsx")


def test_empty_list():
    assert build_file_tree([]) == []


def test_single_child_chain_is_flattened():
    files = [
        _file("frontend/a/b/c/x.ts", is_new=True),
        _file("frontend/a/b/c/y.ts"),
    ]
    rows = build_file_tree(files)
    headers = [row for row in rows if isinstance(row, TreeHeader)]
    assert len(headers) == 1
    assert headers[0].label == "frontend › a › b › c"
    leaves = [row for row in rows if isinstance(row, TreeLeaf)]
    assert [row.label for row in leaves] == ["x.ts", "y.ts"]
    assert [row.depth for row in leaves] == [1, 1]


def test_shorten_path_fits_in_columns():
    assert shorten_path(["a", "b", "c.py"], 30) == "a/b/c.py"

    long = ["frontend", "app", "src", "components", "dashboard"]
    for max_cols in (24, 30):
        result = shorten_path(long, max_cols)
        assert len(result) <= max_cols
        assert result.endswith("dashboard")
        assert "…" in result


def test_shorten_path_single_long_segment_stays_tail():
    result = shorten_path(["".join("x" * 400)], 25)
    assert len(result) <= 25
    assert result.endswith("xxx")


def test_root_files_render_without_directory_header():
    files = [_file("README.md"), _file("pyproject.toml"), _file("src/main.py")]
    rows = build_file_tree(files)
    kinds = [type(row) for row in rows]
    assert kinds.count(TreeLeaf) == 3
    assert kinds.count(TreeHeader) == 1
    assert rows[0].label == "README.md"