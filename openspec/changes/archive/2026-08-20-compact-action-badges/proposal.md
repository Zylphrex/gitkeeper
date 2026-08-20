## Why

The per-row action badges `[awaiting you]`, `[wait: author]`, `[wait: others]` each consume 15 columns of a 36-column row in the PR queue list. Long repository names and author handles are truncated so aggressively that they become barely visible, even though they are the most useful row content for disambiguating PRs.

## What Changes

- Replace the textual action badges in the queue list with single-character glyphs: `●` (awaiting the user), `○` (waiting on others), `◇` (waiting on author), dropping the surrounding brackets entirely.
- Keep the existing color coding (bold cyan for awaiting-the-user rows, dim for waiting rows) as the primary active/not-active signal; the glyph preserves the author-vs-others distinction at a glance.
- Keep the worded action-state lines in the overview pane (`Awaiting your action`, `Waiting on author`, `Waiting on others`) unchanged, so the contextual pane remains an always-accurate legend for the glyphs.
- Reclaim the freed columns for the repository name and author on the metadata row, keeping the same truncation rules.

## Capabilities

### New Capabilities

- none

### Modified Capabilities

- `tui-review-client`: the queue-entry action badge requirement (specs/tui-review-client/spec.md) changes from textual labels (`awaiting you`, `wait: author`, `wait: others`) to single-character glyphs (`●`, `○`, `◇`), and the metadata-row layout is updated to prefer fitting the full repository name and author before truncating.

## Impact

- `gitkeeper/ui/list_view.py`: `ACTION_BADGES` map (line 14-18) becomes glyph-based; `_populate_list` row composition unchanged otherwise.
- `gitkeeper/ui/app.py`: status-bar summary text (`Loaded N awaiting your action · M waiting`) remains worded and unchanged.
- `gitkeeper/ui/overview_view.py`: `ACTION_STATE_LINES` remains worded and unchanged (serves as legend).
- `tests/test_ui.py`: assertions on literal badge strings (test_pr_list_action_badges, lines 273, 332, 355, 454) updated to assert the glyphs.
- No API or dependency changes.
