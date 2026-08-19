## Why

The diff view is currently a blank slate: review threads that already exist on the pull request (comments left by teammates or the user on a previous pass) are never fetched, so a reviewer sees the unified diff as if no conversation had happened. Reloading every diff and re-reading its inline discussion from memory slows down re-review and risks missing prior feedback.

## What Changes

- Fetch existing review threads alongside the diff whenever a PR's diff is loaded, using a GraphQL `reviewThreads` query keyed on repository name/owner and pull request number.
- Cache the fetched threads per PR key, mirroring the existing diff cache.
- Render existing review threads inline on their corresponding diff lines, prefixed with the comment author, visually distinct from the reviewer's own pending (not-yet-submitted) draft comments.
- When a diff line carries both existing review threads and a new pending comment, render both; pending comments and the pending submission count remain unchanged.
- Degrade gracefully if the threads fetch fails: the diff still displays as today and a status message is shown.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `tui-review-client`: Extend the "Inline and Top-Level Commenting" requirement — when a pull request's diff is viewed, the system SHALL display existing review threads attached to their diff lines alongside any of the reviewer's own pending comments.

## Impact

- `gitkeeper/github/queries.py`: new `PULL_REQUEST_THREADS_QUERY` requesting `reviewThreads { path, line, comments { author, body } }`.
- `gitkeeper/github/client.py`: new `ReviewThread`/`ThreadComment` dataclasses and `get_pull_request_review_threads` method; reuses `_execute_query` for auth/retry handling.
- `gitkeeper/ui/app.py`: `_fetch_diff_for_pr` fetches threads in the same worker and populates a `cached_threads` dict alongside `cached_diffs`; `_display_cached_diff` passes threads into the diff viewer.
- `gitkeeper/ui/diff_view.py`: `PRDiffView` holds the authoritative `existing_threads` list and passes it into `DiffViewer.set_file_diff`; `DiffViewer` gains an `existing_by_line` cache rendered in `_render_line` with the author prefix.
- Tests under `tests/` for thread fetching, parsing, and diff rendering.