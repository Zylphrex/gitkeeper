## Why

The queue list renders each PR title as a hard-coded 22-character slice with no ellipsis, sharing its row with a scoring-reason chip that pushes the slice past the panel width and wraps mid-chip. Titles like `fix: restore the consi` are unreadable, and the author is absent from the row entirely, making the queue hard to scan.

## What Changes

- Remove the `(reason)` chip from queue list rows (the full rationale already appears in the overview panel on selection).
- Display the PR author (`@login`) on the first row alongside the tier badge, number, and repository name.
- Display the PR title on its own second line, flush-left, truncated with a trailing ellipsis (`…`) to the row width instead of wrapping or clipping mid-word.
- Truncate pathologically long repository names with an ellipsis so the author always remains visible and rows never wrap.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `tui-review-client`: The *Interactive PR Queue Navigation* requirement currently pins each queue entry to tier label, repository name, and PR number. It changes so entries additionally show the author and a title rendered on its own line, truncated with an ellipsis rather than wrapped.

## Impact

- `gitkeeper/ui/list_view.py`: `_populate_list` row construction — remove the reason chip, add the author span, and replace the fixed `title[:22]` with width-aware ellipsis truncation.
- `gitkeeper/ui/filestree.py`: no change; its `ELLIPSIS`/row-width conventions are mirrored, not imported.
- `tests/test_ui.py`: new assertions for author presence, ellipsized titles, flush-left second line, and absence of reason chips.
- No changes to the scoring pipeline, GitHub client, layout widths, or the diff/overview panes.