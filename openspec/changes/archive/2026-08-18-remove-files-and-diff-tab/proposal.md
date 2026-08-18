## Why

The right panel renders a single-tab `TabbedContent` labeled "Files & Diff" and binds the `2` key to activate that tab. Since the Overview became a persistent right-hand section (`2026-08-18-overview-as-right-section`), the "Files & Diff" tab has no siblings: the tab bar is a redundant label and the `2` shortcut has nothing to switch to. Removing both declutters the layout and frees the `2` key.

## What Changes

- Remove the `2` keybinding (`Binding("2", "tab_diff", "Files & Diff")`) and its footer entry.
- Remove the "Files & Diff" tab bar/label on top of the diff pane by replacing the `TabbedContent`/`TabPane` wrapper around `PRDiffView` with a plain container.
- Remove `action_tab_diff` and the now-constant tab-state checks (`_move_focus` guard, `action_comment_action` branch). The comment action (`c`) always attaches an inline comment to a diff line; submitting a review moves fully to `s`/`a`.
- Update `tests/test_ui.py` call sites that invoke `action_tab_diff`.

## Capabilities

### New Capabilities
_(none)_

### Modified Capabilities
- `tui-review-client`: the diff pane is no longer a tab. The "Files & Diff" tab bar/label and the dedicated pane-switching keybinding (`2`) are removed; the diff content is always visible as a plain, unlabeled pane.

## Impact

- `gitkeeper/ui/app.py`: `BINDINGS`, `compose`, CSS (`#right-tabs`), `_move_focus`, `action_tab_diff`, `action_comment_action`.
- `tests/test_ui.py`: five `app.action_tab_diff()` call sites (lines ~224, 387, 432, 485, 530).
