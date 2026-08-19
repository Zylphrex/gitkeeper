## 1. GraphQL Client

- [x] 1.1 Add `ReviewThread` and `ThreadComment` dataclasses to `gitkeeper/github/client.py` beside `DraftReviewComment`.
- [x] 1.2 Add `PULL_REQUEST_THREADS_QUERY` to `gitkeeper/github/queries.py`: `reviewThreads(first: 100) { nodes { path line comments(first: 20) { nodes { author { login } body } } } }` keyed on `repository(owner, name)/pullRequest(number)`.
- [x] 1.3 Add `GitHubGraphQLClient.get_pull_request_review_threads(repo_name_with_owner, pull_number) -> List[ReviewThread]` parsing the response and skipping threads without a `path`.

## 2. Wire App Fetch Path

- [x] 2.1 Add `self.cached_thread: Dict[str, List[ReviewThread]]` to `GitkeeperApp.__init__` (app.py:113).
- [x] 2.2 In `_fetch_diff_for_pr` (app.py:218), fetch threads after the diff text and store in `cached_thread`; on threads failure, store `[]` and surface a status message without failing the diff.
- [x] 2.3 In `_display_cached_diff` (app.py:192), pass `cached_thread.get(pr_key, [])` through to `PRDiffView.load_diff`.

## 3. Diff View Rendering

- [x] 3.1 Extend `PRDiffView.load_diff(diff_text, existing_threads, draft_comments)` to hold the authoritative `existing_threads` list, reset in `show_loading`/`show_error`, and pass it into every `DiffViewer.set_file_diff` call (diff_view.py:311, 332, 344).
- [x] 3.2 Extend `DiffViewer.set_file_diff` to populate `existing_by_line: Dict[int, List[ThreadComment]]` from the authoritative list filtered by `display_path`, skipping `line is None` threads.
- [x] 3.3 Render existing threads in `_render_line` before the pending block as `      💬 {author}: {body}` with a distinct style from pending comments.

## 4. Tests

- [x] 4.1 Add a client test that `get_pull_request_review_threads` parses the GraphQL payload into `ReviewThread`/`ThreadComment` objects and drops line-less threads.
- [x] 4.2 Add a `DiffViewer`-level test that `set_file_diff` renders existing threads with authors on matching lines and skips unmatched or `line is None` threads.
- [x] 4.3 Add a UI test that a line with both existing threads and a pending comment renders both distinctly, and a threads-fetch-failure test asserting the diff still displays.
- [x] 4.4 Run the full suite (`pytest tests/`) and confirm no regressions.

### Test Summary

- 89 tests pass; 1 pre-existing failure (`test_pr_overview_metadata_wraps_in_panel`) is date-sensitive and fails identically on clean `main` (unrelated to this change).