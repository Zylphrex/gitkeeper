## 1. Viewer status derivation

- [x] 1.1 Add a `ViewerStatus` dataclass in `gitkeeper/scoring/calculator.py` with `has_reviewed`, `verdict`, `verdict_at`, `re_review_due` fields
- [x] 1.2 Add a pure `derive_viewer_status(pr, username) -> ViewerStatus` function that reuses `_latest_my_verdict`, `_latest_my_review_dt`, and `_re_review_due` (or their logic) and returns `None`-safe values
- [x] 1.3 Add unit tests in `tests/test_scoring.py` covering: no reviews, approved verdict, requested-changes verdict, re-review due after author push, and missing/mismatched username case-insensitivity

## 2. Overview status line

- [x] 2.1 Extend `PROverviewView.update_pr` (or add a companion update method) to accept the viewer login, `ViewerStatus`, own thread comment count, and draft comment count
- [x] 2.2 Render a "you" status row in the overview metadata for each state per the spec: not yet reviewed, approved, requested changes, commented with count, optional re-review indicator, and pending draft count
- [x] 2.3 Keep the row absent (fall back to today's rendering) when the viewer login is unknown
- [x] 2.4 Wire `app._select_pr` to build the `ViewerStatus` from `scored_pr.pr` + `self.config.github.user` and compute comment counts from `cached_thread[pr_key]` and `draft_comments[pr_key]` before updating the overview

## 3. Diff thread emphasis

- [x] 3.1 Add a `viewer_login: Optional[str]` parameter to `PRDiffView.load_diff` and `DiffViewer.set_file_diff`
- [x] 3.2 Update `DiffViewer._render_line` to render threads authored (case-insensitively) by the viewer as a distinct "You" styled line, while other threads render as today
- [x] 3.3 Ensure `viewer_login == None` renders exactly as today (no behavioral change when unknown)

## 4. Live updates and refresh wiring

- [x] 4.1 Re-render the overview's status row from `_display_cached_diff` when threads finish loading so the comment count appears without reselecting the PR
- [x] 4.2 Add or extend async UI tests in `tests/test_ui.py` covering: overview status line contents for reviewed/unreviewed PRs, and own-thread styling in the diff view
- [x] 4.3 Run the full test suite (e.g. `pytest`) and confirm no regressions