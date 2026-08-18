## 1. GitHub client data model

- [x] 1.1 Add `baseRefName` and `headRefName` to the PR fragment in `gitkeeper/github/queries.py` inside `REVIEW_REQUESTS_QUERY`
- [x] 1.2 Add optional `base_ref: Optional[str] = None` and `head_ref: Optional[str] = None` fields to `PullRequestData` in `gitkeeper/github/client.py`
- [x] 1.3 Parse `baseRefName` / `headRefName` from each search node in `fetch_pending_review_requests` and pass them into `PullRequestData`
- [x] 1.4 Update `REVIEW_REQUESTS_QUERY` mocked GraphQL response fixtures in `tests/test_github_client.py` to include the new fields and assert `base_ref` / `head_ref` parsing

## 2. Overview layout and wrapping

- [x] 2.1 Change `#pr-meta-box` and `#pr-score-box` in `gitkeeper/ui/overview_view.py` from `Vertical` (`height: 1fr`) to `VerticalGroup` (`height: auto`) so they hug their content
- [x] 2.2 Add `width: 1fr` to the title, meta, score rationale, and breakdown labels so long lines wrap at the panel edge instead of clipping
- [x] 2.3 Add `text-overflow: ellipsis` to the meta label CSS so unbreakable long tokens end with `…` instead of a silent cut

## 3. Enriched metadata rendering

- [x] 3.1 Add a CI-state color helper mapping SUCCESS/FAILURE/ERROR/PENDING/other to rich colors
- [x] 3.2 Add a relative-time helper formatting ISO-8601 timestamps as `Updated: 1h ago` etc. (defensive parsing via try/except)
- [x] 3.3 Restructure `update_pr()` in `overview_view.py` to compose the stacked metadata rows from design.md Decision 3, including the optional branch-refs row from the new `base_ref`/`head_ref` fields
- [x] 3.4 Add the requested-reviewers row (capped at 3 with `+N more`) and the existing-reviews summary row (e.g. `2 ✓ · 1 ✗`) using the already-fetched `requested_reviewers` and `reviews` lists
- [x] 3.5 Keep the `[DRAFT]` badge in the title line; preserve score rationale and breakdown rows unchanged

## 4. Tests and verification

- [x] 4.1 Extend `tests/test_ui.py` to cover the overview layout with a long metadata fixture (wrapping asserted via rendered-screen match at a pinned 44x40 size) and state-based assertions for the new rows
- [x] 4.2 Add unit tests for the CI color helper and the relative-time helper (including missing/malformed timestamps)
- [x] 4.3 Run the full test suite via `pytest` and verify no regressions
- [x] 4.4 Manually render the app (or a `PROverviewView` demo) at 44- and 40-column widths to confirm all metadata remains on-screen and wraps