## Context

See proposal.md — Why. Today the diff pane renders only the unified diff plus the reviewer's own pending drafts: `PRDiffView` holds the parsed `file_diffs`, the local `draft_comments`, and the authoritative `existing_threads` will live beside them; `DiffViewer.set_file_diff` builds a per-file `comments_by_line` cache used by `_render_line` (gitkeeper/ui/diff_view.py:115-171). The GitHub client already wraps all GraphQL calls through `_execute_query` (retries, 401 → PermissionError) and uses REST only for the raw diff text (gitkeeper/github/client.py:265-275). The diff for a PR is fetched in the `@work(exclusive=True, thread=True)` worker `_fetch_diff_for_pr` and cached by PR key in `cached_diffs` (gitkeeper/ui/app.py:218-230).

## Goals / Non-Goals

**Goals:**
- Fetch and cache existing review threads alongside the diff, once per PR view, reusing the existing worker and cache patterns.
- Render threads on their diff lines, labeled with author, visually distinct from the reviewer's pending drafts.
- Keep the pending-comment flow and submission count untouched.

**Non-Goals:**
- Top-level review bodies or PR issue comments (separate fetch path, not inline threads).
- Replying to existing threads or editing them.
- Pagination beyond a single `reviewThreads(first: 100)` page.
- Refreshing thread data during a session beyond the diff-cache lifetime (mirrors existing diff staleness).

## Decisions

### Decision 1: GraphQL `reviewThreads`, not REST reviews
- **Decision**: Add a `PULL_REQUEST_THREADS_QUERY` using `repository(owner, name)/pullRequest(number)/reviewThreads(first: 100)`, and a client method `get_pull_request_review_threads(repo_name_with_owner, pull_number) -> List[ReviewThread]` returning new dataclasses `ReviewThread(path, line, comments)` and `ThreadComment(author, body)`.
- **Rationale**: `reviewThreads[].line` is the new-file line number — the same convention `_line_target_no` already uses for drafts and that GitHub's own `threads` mutation input accepts. REST's `position`/`original_line`/`side` fields are a mismatch to rendered rows and add parsing surface. GraphQL also rides the existing `_execute_query` auth/retry path.
- **Alternative considered**: REST `GET /reviews` — rejected for line-identity ambiguity. Adding `reviewThreads` to `REVIEW_REQUESTS_QUERY` — rejected: bloats every queue refresh with thread bodies for 25 PRs when only the viewed PR needs them.

### Decision 2: Threads cached per PR key beside `cached_diffs`
- **Decision**: In `_fetch_diff_for_pr`, after fetching the diff text, call `get_pull_request_review_threads` and store the result in a new `cached_threads: Dict[str, List[ReviewThread]]`. If the threads call fails, store `[]`, keep the diff, and surface a status message; the diff flow must not depend on the threads fetch succeeding. `_display_cached_diff` passes the threads into `PRDiffView.load_diff(diff_text, threads, drafts)`.
- **Rationale**: Both fetches are for the same PR in the same worker; one loading lifecycle. Thread staleness semantics then match the existing diff cache exactly (stale until app restart / next diff trigger), which is acceptable and consistent. Failure isolation keeps the core review flow resilient.
- **Alternative considered**: A separate worker/refresh trigger for threads — more latency and lifecycle states for no immediate benefit.

### Decision 3: List ownership at PR level, cache at viewer level
- **Decision**: `PRDiffView` holds the authoritative `existing_threads: List[ReviewThread]` (reset in `show_loading`/`show_error`, filtered by `display_path` in `set_file_diff` exactly like drafts). `DiffViewer` keeps `comments_by_line` for pending drafts untouched and adds a parallel `existing_by_line: Dict[int, List[ThreadComment]]`, rendered in `_render_line` before the pending block.
- **Rationale**: File switching re-runs `set_file_diff` and re-derives the per-file cache from the authoritative list, matching the existing draft pattern (decision 3 of the prior change) with minimal new state. Keeping the two caches separate avoids touching the just-shipped pending-comment rendering.
- **Visual distinctness**: existing threads render as e.g. `      💬 {author}: {body}` in one style; pending drafts keep the current `💬 Pending Comment: {body}`. Both appear on the same row when a line has both (spec scenario "Existing threads and pending comment on the same line").

### Decision 4: Line matching degrades silently
- **Decision**: Match threads by comparing `thread.line` to `_line_target_no(line)` (prefers `new_line_no`). Threads with `line is None` (left-side/deleted-line threads) or whose line matches no rendered row are not displayed — per spec "threads whose target line cannot be matched to a rendered diff line SHALL NOT be displayed".
- **Rationale**: Identical matching logic to drafts; a mismatched thread (e.g. after a force-push made it outdated) is safer to omit than to render on the wrong line.

## Risks / Trade-offs

- **[Risk] Thread count exceeds one page (`first: 100`)** → Only the first 100 threads render. **Mitigation**: acceptable for typical PRs; pagination is a documented follow-up.
- **[Risk] Thread fetch failure appears as "no comments"** → The diff still renders and a status message names the failure; cached `[]` prevents repeated retries per key. **Mitigation**: covered by spec scenario and tests.
- **[Risk] Row height grows with long/multi-comment threads** → Same reflow behavior as the existing pending label; `OptionList` handles it deterministically. **Mitigation**: verify with rendering tests.
- **[Risk] Outdated threads after force-push** → Match by line usually fails, so they hide rather than misplace. **Mitigation**: accepted; `isOutdated` is not explicitly filtered.

## Migration Plan

No deployment or rollback steps: in-app behavior change with no stored state.