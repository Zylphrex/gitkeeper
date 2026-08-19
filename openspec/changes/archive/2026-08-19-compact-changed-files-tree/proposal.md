## Why

The changed-files list in the diff viewer renders full paths as flat rows in a 32-column pane. Long paths wrap onto multiple lines, making the list ragged and difficult to scan — the filenames that matter get buried in repeated pure prefixes (`frontend/app/src/...`, `gitkeeper/...`).

## What Changes

- Replace the flat `[ADD]/[MOD]/[DEL]/[REN]`-prefixed full-path rows in the file list with a compact file tree.
- Tree nodes group files under their directories; directory headers are non-navigable focus "landmarks" (rendered as disabled `OptionList` rows).
- Single-child path chains are flattened onto one row so deep spines never cost indentation width (e.g. `▾ frontend › src › components`).
- Each file row keeps its change-type badge and displays the **filename plus enough of its directory tail to stay parseable**; rows SHALL NOT wrap.
- Empty-tree/list edge cases (no files, single file, unreadable diff) render without wrapping or clutter.
- The `/` filename search and existing focus zones keep working against the same underlying file list, including filtered results rendered as the same compact tree.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `tui-review-client`: the In-TUI Diff Viewer requirement changes such that the changed-files list renders as a non-wrapping compact directory tree with flattened single-child paths, preserving search and focus behavior.

## Impact

- `gitkeeper/ui/diff_view.py` — `PRDiffView.load_diff`, `filter_files`, `clear_filter` rendering path; `DiffViewer` unchanged
- New tree-building helper (pure function) likely in `gitkeeper/diff/parser.py` or a new `gitkeeper/ui/filestree.py`
- `gitkeeper/ui/app.py` — unchanged (focus zones keep targeting `file-option-list`)
- Existing specs: delta to `openspec/specs/tui-review-client/spec.md`
- No CLI, API, or GitHub client changes