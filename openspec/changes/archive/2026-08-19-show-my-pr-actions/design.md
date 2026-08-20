## Context

See proposal.md for motivation. The relevant current state:

- `PullRequestData.reviews[]` already carries `author`, `state`, `submitted_at` for every review on the PR; `pushed_at` gives the latest author push.
- `scoring/calculator.py` already computes the viewer's latest verdict (`_latest_my_verdict`), latest act time (`_latest_my_review_dt`), and re-review-due flag (`_re_review_due`), but these are private and only feed band placement, never the UI.
- `gitkeeper/ui/app.py` holds the session state the overview cannot see: `cached_thread[pr_key]` (fetched thread comments per PR) and `draft_comments[pr_key]`.
- `PROverviewView.update_pr(scored_pr)` renders metadata rows purely from the scored PR; it has no viewer context.
- `DiffViewer._render_line` stamps every thread as `author: body` with no way to tell who is speaking.

## Goals / Non-Goals

**Goals:**
- A "your status" line in the overview panel that derives directly from data GitHub already returns.
- Own-authored diff threads visually distinguishable from everyone else's.
- In-session draft comment counts reflected in the status without extra fetches.

**Non-Goals:**
- No changes to GitHub queries, mutations, or data models — the needed fields already exist.
- No persistence/cross-session history tracking; drafts remain session-scoped.
- No queue-list row changes (band placement already reflects turn state).

## Decisions

### 1. Status derivation lives in `calculator.py`, exposed as `ViewerStatus`
Add a `ViewerStatus` dataclass and a pure `derive_viewer_status(pr, username)` function that reuses the existing private helpers (`_latest_my_verdict`, `_latest_my_review_dt`, `_re_review_due`) or their logic:

```
ViewerStatus(
  has_reviewed: bool
  verdict: Optional[str]          # APPROVED / CHANGES_REQUESTED / DISMISSED
  verdict_at: Optional[datetime]
  re_review_due: bool
)
```

*Why here:* it is headless, unit-testable in `test_scoring.py`, and mirrors where turn-state logic already lives. Alternatives rejected: formatting ad hoc in the overview view (untestable, mixes presentation with logic), or adding it to `ScoredPullRequest` (the status is not a scoring input and would overload the dataclass).

### 2. The app composes the status line; the overview stays presentation-only
- On selection, `app._select_pr` builds the `ViewerStatus` from `scored_pr.pr` + `self.config.github.user`, and passes it plus `own_thread_count` (from `cached_thread[pr_key]`) and `draft_count` (from `draft_comments[pr_key]`) into `overview_view.update_pr(...)`.
- When threads finish loading, `_display_cached_diff` triggers a lightweight overview re-render so the comment count appears "once threads are loaded" per the spec, without reselecting the PR.
- **Alternative considered:** overview deriving everything itself — rejected because `PRListView` has no config access and thread/draft counts live in app state.

### 3. Own-thread emphasis relies on the viewer login, threaded into the diff view
`PRDiffView.load_diff` and `DiffViewer.set_file_diff` gain a `viewer_login: Optional[str]` parameter. `_render_line` compares each thread author case-insensitively and renders the viewer's own as a "You" line in accent style, others stay as today. Falls back to today's rendering when `viewer_login` is `None` (viewer unknown).

### 4. No timing/ordering changes to diff fetching
Threads are fetched per-PR once and cached (`cached_thread[pr_key]`); the placeholder comment count is zero until a diff is loaded, which matches the spec's "once diff threads are loaded" wording. No new lazy-load path is introduced.

## Risks / Trade-offs

- **Viewer login may be `None`** (never refreshed, or `get_viewer_login` failed) → the status line falls back to omitting itself and own-threads render inline, exactly like today. No crash path.
- **Re-review flag depends on `pushed_at`** which comes from the last commit; if `pushed_at` is missing the flag is simply false. Same fallback behavior as the existing band logic.
- **Comment count reflects only the current PR's cached threads** — a PR whose diff was never opened shows `0` threads until loaded. That is faithful to what is known, and the overview updates when threads arrive.
- **Case handling** for logins is applied consistently with existing code (`.lower()` comparisons) so `viewer` vs `Viewer` don't dual-count.

## Migration Plan

TUI-internal change with no persistence. Land the calculator helper (pure functions) first, then the overview/app wiring, then the diff view styling. No rollback story beyond reverting the diff.

## Open Questions

- Exact copy for the status line variants (e.g. `✓ approved`, `✗ requested changes`, `commented ×3`, `not yet reviewed`, `— new pushes since review`). Cosmetic; safe to settle during implementation.