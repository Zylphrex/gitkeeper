## 1. Overview layout split

- [x] 1.1 Rewrite `PROverviewView.compose()` in `gitkeeper/ui/overview_view.py` to render a horizontal row: the meta box stacked above the score box on the left, the description markdown on the right, instead of the current vertical stack ending in a scroll
- [x] 1.2 Remove the `VerticalScroll` shell from the description column so the body renders as a non-scrollable fixed preview
- [x] 1.3 Keep the debounce + exclusive markdown worker path (`_schedule_markdown` / `_update_pr_markdown`) intact, updating only the container ids it queries
- [x] 1.4 Confirm `update_pr()` renders into the new left (meta + score) and right (description) panels with no change to the metadata row content

## 2. App-level container restructure

- [x] 2.1 In `gitkeeper/ui/app.py`, restructure `compose()` so the overview mounts as a full-width bottom row containing the two columns from task 1.1, below the PR list + diff panes
- [x] 2.2 Size the bottom row so it reaches ~16 rows on normal terminals and ~40% of the window on very short ones (`height: 40%; max-height: 16`), and remove the overview's 44-column width and border-left from the main layout
- [x] 2.3 Verify `FOCUS_GRAPH`, `WIDGET_TO_ZONE`, and zone-scoped actions in `app.py` are unchanged since the description is not a focus target
- [x] 2.4 Remove any overview-column carve-out in `list_view.py` row-width accounting now that the PR list no longer neighbors the overview, and confirm the diff pane expands to the freed width

## 3. Spec updates (after review)

- [x] 3.1 Update `openspec/specs/tui-review-client/spec.md` per the delta specs: overview in a fixed-height bottom row, meta left + description right, description non-scrollable with no keyboard shortcut to it
- [x] 3.2 Update `openspec/specs/vim-navigation/spec.md` to drop "overview body" from the scrollable-widget list for `j`/`k` motion
- [x] 3.3 Run `openspec validate --check move-pr-overview-to-bottom` once implementation is complete

## 4. Behavior verification

- [x] 4.1 Run the existing test suite under `tests/` (e.g. `pytest`) to confirm no TUI-layout regression surfaces
- [x] 4.2 Eyeball the app on a ~100-column terminal: overview in bottom row, meta left / description right, no overview scrollbar, diff pane spans full width in the top row
- [x] 4.3 On a narrow ~60-column terminal, confirm PR-list rows stay two rows tall without wrapping and the description column budget behaves like the old clamped width