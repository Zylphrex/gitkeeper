## Why

When the PR queue outgrows the left pane and the list becomes scrollable, a vertical scrollbar appears inside the option list and steals 2 columns that the row-width budget never accounted for. Rows sized to the non-scrollable width then exceed the actual render width and soft-wrap, so some entries degrade into 3-4 visual rows: repo names truncated too early, author handles stranded on their own row, and titles split across lines instead of a clean trunkated single line.

## What Changes

- Fix the row-width budget so it is computed from the width each option line actually renders at (`scrollable_content_region`), not the wider `content_region`.
- Keep the invariant that every queue entry renders as exactly two rows: a metadata row (`[tier] #num repo  @author`) and a single-line truncated title.
- Guard against the scrollbar appearing/disappearing mid-session (no resize event fires) so the layout never re-breaks when the list grows or shrinks.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `tui-review-client`: strengthen the "Interactive PR Queue Navigation" requirement so every queue entry renders as exactly two rows regardless of queue length (i.e., independent of scrollbar visibility), with repo/author metadata truncated to fit the available render width.

## Impact

- `gitkeeper/ui/list_view.py` — `_effective_row_width` and row-budget math in `_populate_list`; possibly `ROW_WIDTH`/reserve logic.
- Tests in `tests/test_ui.py` — existing two-row invariants keep covering the non-scrollable case; new fixtures pin the scrollable (long-queue) case.
- No changes to data model, GitHub client, or scoring.