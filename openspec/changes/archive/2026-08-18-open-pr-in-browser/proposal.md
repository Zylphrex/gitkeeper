## Why

Reviewers triaging PRs inside the full-screen TUI frequently need to jump to GitHub to see the full conversation, CI checks, or comments. Currently the TUI shows the PR number and title but offers no way to reach the PR's GitHub page — neither a clickable link nor a keybinding — so reviewers must exit the TUI or construct the URL by hand. The PR URL (`pr.url`) is already fetched by the GitHub client, so surfacing it costs nothing.

## What Changes

- Render the selected PR's number as a clickable terminal hyperlink (OSC 8) to its GitHub URL in the overview header, matching the hyperlink behavior the non-TUI terminal table previously provided.
- Render the PR number in the left queue list as a hyperlink to its GitHub URL.
- Add an `o` keybinding that opens the currently selected PR in the default web browser via `App.open_url` (which maps to `webbrowser.open` on terminal drivers).
- When a PR has no URL, render the plain `#<number>` text and have `o` report that no URL is available instead of opening anything.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `tui-review-client`: Add requirements for a clickable PR hyperlink in the overview and queue list, plus an `o` keybinding to open the selected PR in the default browser.

## Impact

- **Affected code**: `gitkeeper/ui/app.py` (new binding + `open_browser` action), `gitkeeper/ui/overview_view.py` (hyperlink on title), `gitkeeper/ui/list_view.py` (hyperlink on row), and TUI tests in `tests/test_ui.py` / `tests/test_overview_view.py`.
- **Dependencies**: Textual `App.open_url` (delegates to `webbrowser.open`); Rich `[link=URL]text[/link]` markup and `link` text style (OSC 8). No new dependencies.
- **Backwards Compatibility**: Fully backward compatible. Terminals without OSC 8 hyperlink support render the plain `#<number>`; the `o` binding is additive.
