## Context

See proposal.md — Why. The changed-files list is an `OptionList` (`#file-option-list`) inside a 32-column pane (`diff_view.py:187`). Rows are built by identical badge+path code duplicated in three places: `load_diff` (diff_view.py:270-278), `filter_files` (309-317), and `clear_filter` (330-338). `OptionList` wraps option text wider than the pane, which is the visible bug. The app's `/` search and focus graph (app.py:24-28) are keyed to the `file-option-list` widget id and an `Option` per file whose `option_index` maps directly onto `self.file_diffs[idx]` (diff_view.py:288-293).

## Goals / Non-Goals

**Goals:**
- Every file-list row renders on a single line with the filename plus minimal directory context.
- Directory grouping appears without breaking the existing selection, `/` search, or `h`/`l` focus flow.
- Reuse the codebase's existing `disabled=True` Option pattern (already used for loader rows, diff_view.py:72).

**Non-Goals:**
- Not building an interactive expand/collapse tree (no arrow-left collapse, no persistent open/closed state).
- Not changing the diff viewer, overview, or PR list panes.
- Not altering `DiffViewer` or the diff-line search.

## Decisions

**1. "Fake tree" in the existing OptionList over Textual's `Tree` widget.**
Header rows are regular `Option(..., disabled=True)` entries; file rows follow. Rationale: keeps every integration point — `/` search (`filter_files`), focus zones in app.py, `file_{idx}` selection mapping, and the cached `on_option_list_option_highlighted` handler — intact. An interactive `Tree` would require reworking all of those for marginal benefit (see Non-Goals). Alternative considered: Textual `Tree` — rejected because it changes the widget identity, breaks `WIDGET_TO_ZONE`, and adds collapse complexity with no requirement behind it.

**2. Single shared row-builder to replace the three duplicated render blocks.**
New module `gitkeeper/ui/filestree.py` exposes `build_file_tree(file_diffs) -> List[TreeRow]` where `TreeRow` is either a header (directory chain, `disabled=True`) or a leaf (a file `Option` with badge + shortened path) carrying a `file_index` back into `file_diffs`. All three call sites (`load_diff`, `filter_files`, `clear_filter`) render via it. Rationale: the triad of duplicated render blocks is the root maintenance hazard; one pure function is unit-testable.

**3. Selection mapping decoupled from `option_index`.**
With header rows interspersed, `event.option_index` no longer equals the `file_diffs` index. `build_file_tree` returns leaves with explicit `file_index`; the handler resolves `file_diffs[row.file_index]` instead of trusting `option_index`. Disabled header rows are skipped by the cursor, but the option row still occupies an index slot, so the mapping is required regardless. Filters re-run `build_file_tree` over `matching`, so `filter_files`/`clear_filter` stay symmetrical.

**4. Path shortening: keep the tail, ellipsize in the middle.**
Leaf rows render `badge + parent/filename` (last two path segments), prefixed with `…/` when deeper segments are dropped; header rows render the flattened single-child chain (see Decision 5) shortened the same way. A `shorten_path(segments, max_cols)` helper guarantees any row fits `#file-option-list` width so nothing can wrap. This choice comes from the original pain: a hard right-slice (`[:27]`) kills filenames; eliding the middle keeps the discriminating parts.

**5. Flattened single-child chains.**
Build paths as a segment trie. A directory node with exactly one child directory is folded into the parent's label with a ` › ` separator (e.g. `▾ frontend › src › components`), so deep spines never consume indentation. The rendered header is then tail-shortened (Decision 4). Directories with ≥2 distinct children become separate header rows; files are leaves.

## Risks / Trade-offs

- **Textual disabled-row cursor behavior may vary by version** → the selection mapping (Decision 3) makes correctness independent of whether the cursor skips disabled rows.
- **Header chains can still exceed the pane on very deep repos** → `shorten_path` guarantees a single line by sacrificing leading segments (`… › src › components`); the filename always survives.
- **Two files sharing parent+name stay indistinguishable** → acceptable for a triage list; the `/` search and full path remain available via selection → diff viewer header.
- **Common-prefix monotony across the whole list** (all files under one root) → the tree structurally hoists the root into a header, which also compresses the file rows; same win described in the proposal.

## Migration Plan

Pure TUI change with no deployed state or API. Rollback is reverting the diff; behavior fully restores when the previous renderer is back.