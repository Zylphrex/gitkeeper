## 1. Whitespace-Insensitive Re-derivation

- [x] 1.1 Add `gitkeeper/diff/whitespace.py` with `hide_whitespace(file_diffs: List[FileDiff]) -> List[FileDiff]`: re-split a hunk into `old_lines` (context + `-`) and `new_lines` (context + `+`), run an LCS alignment whose equality is `re.sub(r"\s+", "", a) == re.sub(r"\s+", "", b)`, and emit context rows for ws-equal pairs (content from the new side, carrying both line numbers), untouched `-`/`+` pairs otherwise, and unpaired rows as added/deleted.
- [x] 1.2 Drop any hunk whose every change row collapsed to context; keep a `FileDiff` whose hunks all dropped in the output (the viewer renders its empty state).
- [x] 1.3 Ensure line numbers on emitted rows reuse the original parser-assigned numbers rather than re-numbering subsequent rows.

## 2. View Toggle and Key Binding

- [x] 2.1 Add a reactive `hide_whitespace_active: bool = False` (or equivalent) to `PRDiffView` (gitkeeper/ui/diff_view.py:220), storing the authoritative parsed list (`self._parsed_diffs`) when `load_diff` parses, and a method that re-derives `self.file_diffs = hide_whitespace(self._parsed_diffs)` (or the parsed list when inactive) and re-renders the file list + selected file.
- [x] 2.2 Wire the re-derivation into the render path so toggling works from any file and any file-filter state: clear any active `/`-file filter before re-rendering, matching the existing `clear_filter` semantics.
- [x] 2.3 Add `Binding("w", "hide_whitespace", "Hide Whitespace")` to `GitkeeperApp.BINDINGS` (gitkeeper/ui/app.py:75) with an `action_hide_whitespace` that flips the toggle on `PRDiffView` and does nothing when no PR diff is loaded.
- [x] 2.4 Render the active-state indicator in the `DiffViewer` header (gitkeeper/ui/diff_view.py:74): append a ` · whitespace hidden` marker when the mode is active and remove it when not.

## 3. DiffViewer Empty State for Whitespace-Only Files

- [x] 3.1 When the selected `FileDiff` has no hunks left after `hide_whitespace`, render an explicit "no visible changes — whitespace only" note in `DiffViewer.set_file_diff` instead of a blank pane.

## 4. Tests

- [x] 4.1 Add parser-level tests in `tests/test_diff_parser.py` covering: a trailing-whitespace-only hunk collapses to context; a whole-file reindent collapses to context; an interleaved hunk with one real change keeps the real pair and collapses the ws pair; a fully-collapsed hunk is dropped; line numbers survive accounting.
- [x] 4.2 Add a `git diff -w` oracle test (`tests/test_whitespace.py`): craft before/after file fixtures, run `git diff` (and `git diff -w`) on them with `git`'s tools, apply `hide_whitespace` to the default-mode parse, and assert the emitted context/changed classification and line numbers match `git diff -w`'s visible rows for the same fixtures.
- [x] 4.3 Add UI tests in `tests/test_ui.py`: pressing `w` toggles the flag and re-renders (asserting a ws-only hunk disappears from the rendered options and the header indicator appears); pressing `w` again restores the original rows.
- [x] 4.4 Run the full suite (`pytest tests/`) and confirm no regressions.