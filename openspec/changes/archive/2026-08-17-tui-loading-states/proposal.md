## Why

When launching the TUI review client or pressing `r` to refresh the pull request queue, network requests to GitHub and local relevance scoring run asynchronously without clear, non-blocking visual feedback. Adding a dedicated top header with real-time status indicators, timestamp tracking, and explicit diff loading states ensures users always know what background tasks are executing while keeping the interface responsive and interactive.

## What Changes

- Introduce a custom top header widget (`AppHeader`) displaying the application title, active background operations (e.g. fetching GitHub review requests, evaluating local relevance heuristics), and the "Last refreshed: HH:MM:SS" timestamp.
- Provide a non-blocking queue refresh flow that preserves current PR list navigation and selection without blocking user interaction or wiping the screen during re-fetch.
- Display loading indicators and error states in the diff viewer when fetching pull request patches asynchronously.

## Capabilities

### Modified Capabilities
- `tui-review-client`: Add requirements for non-blocking queue refresh status indicators, last refreshed timestamps, and asynchronous diff loading states.

## Impact

- Affected files: `gitkeeper/ui/app.py`, `gitkeeper/ui/diff_view.py`, and a new header widget in `gitkeeper/ui/header.py` (or within `gitkeeper/ui/app.py`).
- Tests: `tests/test_ui.py` to cover header status transitions, diff loading state rendering, and refresh queue callbacks.
