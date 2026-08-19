## 1. File Tree Builder

- [x] 1.1 Create `gitkeeper/ui/filestree.py` with `TreeRow` (header/leaf variants) and `build_file_tree(file_diffs) -> List[TreeRow]`, building a segment trie from each `FileDiff.display_path` and returning headers interleaved in path order with leaf rows carrying a `file_index` back into `file_diffs`
- [x] 1.2 Implement flattened single-child chains: a directory node with exactly one child directory renders as one header row with a ` › ` separator, so deep spines never emit multiple rows
- [x] 1.3 Add `shorten_path(segments, max_cols)` helper that keeps the tail segments (leaf rows: `parent/filename`; header rows: tail of the flattened chain), eliding middle segments behind `…/` so any row fits `#file-option-list` width
- [x] 1.4 Unit-test `build_file_tree` in `tests/test_filestree.py`: multi-file tree with headers, single-file list (no headers), empty list, single-child chain flattening, selection of file rows with correct `file_index` despite interspersed headers

## 2. Wire into Diff View

- [x] 2.1 Extract the duplicated badge+path rendering from `load_diff`, `filter_files`, and `clear_filter` (diff_view.py) into one shared renderer that feeds `build_file_tree` output (badges `[ADD]`/`[MOD]`/`[DEL]`/`[REN]`) into `#file-option-list`
- [x] 2.2 Update `on_option_list_option_highlighted` (diff_view.py:288) to resolve the selected file via the leaf's `file_index` instead of assuming `option_index` maps onto `file_diffs`
- [x] 2.3 Ensure `filter_files`/`clear_filter` re-render the filtered set through the same builder so `/` search results keep the compact tree shape
- [x] 2.4 Verify an empty file list (`self.file_diffs` empty) shows a single non-wrapping placeholder without directory headers

## 3. Guardrails & Verification

- [x] 3.1 Add `overflow-x: hidden` (or equivalent) to `#file-option-list` CSS as a safety net against any residual wrapping
- [x] 3.2 Run `uv run pytest` and confirm existing test suites (especially `test_ui.py`, `test_diff_parser.py`) pass, adding any snapshot/assertions for the new list rendering
- [x] 3.3 Manually smoke-test in the TUI: a→j→k navigation skips header rows, `h`/`l` focus switching, `/` file search over a deep multi-dir PR with no wrapped rows