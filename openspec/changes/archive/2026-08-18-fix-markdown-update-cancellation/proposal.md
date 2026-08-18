## Why

Rapid PR-list navigation followed by quit triggers `_GatheringFuture exception was never retrieved` / `CancelledError` noise from Textual's `Markdown.update()`: `PROverviewView.update_pr` calls `Markdown.update(...)` synchronously and drops the returned `AwaitComplete`, so queued markdown re-parses get cancelled at shutdown with nobody to consume the cancellation.

## What Changes

- Route the PR-body `Markdown.update()` call through an exclusive async worker that awaits the returned `AwaitComplete`, so superseded updates are cancelled cleanly and their `CancelledError` is retrieved by the framework rather than leaked.
- Skip redundant overview re-renders: if the same PR is re-selected, or the PR body text is unchanged since the last render, do not re-parse or re-mount the markdown.
- Keep all non-markdown metadata updates (title, meta, rationale, breakdown) synchronous and immediate.
- Add a regression test covering rapid selection changes followed by app shutdown, asserting no unhandled runner/CancelledError warnings are emitted.

## Capabilities

### New Capabilities

(none)

_none_
### Modified Capabilities

- `terminal-interface`: PR overview rendering must not leak unhandled asyncio cancellation errors during rapid navigation or shutdown, and must avoid redundant markdown re-parses for unchanged selections/bodies.

## Impact

Affected code:

- `gitkeeper/ui/overview_view.py` — `markdown_view.update()` call is fire-and-forget; must move behind an exclusive worker.
- `gitkeeper/ui/app.py` — `GitkeeperApp._select_pr()` re-renders on every highlight event, including re-selecting the same PR.
- `tests/test_ui.py` — new regression test for the cancellation path.

No new dependencies. Relies on Textual worker semantics already used elsewhere in the app (`@work(exclusive=True, thread=True)`).