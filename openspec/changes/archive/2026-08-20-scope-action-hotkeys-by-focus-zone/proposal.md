## Why

The global action hotkeys (`c` comment, `s` submit review, `w` hide whitespace) currently work from every focus zone and are always shown in the footer, even though three of them only make sense while inspecting the diff pane. A reviewer navigating the PR list sees six keys and can accidentally trigger an action mid-flight (e.g. `w`) that has no meaning for the list zone. Scoping the actions to the pane that actually uses them makes the footer truthful and prevents accidental keystrokes.

## What Changes

- The `c`, `s`, and `w` action keys SHALL only be available (bound and shown in the footer) while focus is in the right-hand diff/file pane zone (`file-option-list` or `diff-options`).
- While focus is in the PR list zone (or no widget is focused), the `c`, `s`, `w` keys SHALL be hidden from the footer and SHALL have no effect.
- `q` (quit), `r` (refresh), and `o` (open in browser) remain global — they describe the pull request, not a pane.
- The gate is based on focus zone only, not on whether a diff is currently loaded; existing action guards (e.g. "No PR diff loaded.") continue to handle empty states.
- Existing keyboard layout, key names, and footer ordering are unchanged.

## Capabilities

### New Capabilities
<!-- None: no new spec files created. -->

### Modified Capabilities
- `tui-review-client`: The interactive TUI's action hotkeys become focus-zone-scoped — `c`, `s`, `w` are bound/shown only in the right diff pane, hidden and inert in the PR list zone.

## Impact

- `gitkeeper/ui/app.py` — small change: add a `check_action` override that returns `False` for the scoped actions while the active zone is not a right-pane zone.
- `gitkeeper/ui/modals.py` — unchanged; modals are unaffected because their widget trees never include the diff pane.
- Documentation generated from the footer (key hints) automatically reflects the scoped set via Textual's `active_bindings`.
- Tests: two existing whitespace-toggle tests press `w` from the default (PR list) focus and must be updated to focus a diff/file-list pane first; new tests assert scoped availability in both zones.