## Why

The TUI's background-progress feedback looks frozen: the header status ("Fetching review requests from GitHub...") and the diff view's loading state render a single static braille glyph (`⠋`) that never animates, while the header imports Textual's `LoadingIndicator` widget but never uses it. A slow GitHub fetch or diff load reads as a hang rather than in-progress work, making the interface feel unresponsive.

## What Changes

- Add a shared animated spinner mechanism that cycles braille frames (e.g. `⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏`) while a background operation is active.
- Replace the static `⠋` in the `AppHeader` active-status message with the live animated frame whenever the header is in its loading state.
- Replace the static `⠋` in the diff view's `show_loading` state with the same animated spinner, started on loading and stopped when a diff loads or errors.
- Remove the dead `LoadingIndicator` import from `gitkeeper/ui/header.py`.
- The bottom status bar remains plain text without an animated indicator.

## Capabilities

### New Capabilities

None.

### Modified Capabilities
- `tui-review-client`: Strengthen the "Top Header Status and Refresh Tracking" and "Diff View Asynchronous Loading State" requirements so loading indicators manifest as *animated* spinners that run only while background work is active.

## Impact

- New file: `gitkeeper/ui/spinner.py` with the shared braille frames and an animation mixin.
- Modified: `gitkeeper/ui/header.py` (animated active status, remove unused `LoadingIndicator` import), `gitkeeper/ui/diff_view.py` (`show_loading` uses the spinner, stopped on load/error).
- Tests: `tests/test_ui.py` — the loading-state assertions must match the new frame-based rendering.
- No changes to the network layer, scoring pipeline, or status-bar behavior.