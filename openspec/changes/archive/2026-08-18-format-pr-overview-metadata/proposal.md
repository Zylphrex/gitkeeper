## Why

The TUI's PR overview panel clips metadata instead of formatting it: `Label` widgets in the overview are `width: auto`, so long lines (PR titles, the repo/author/changes/CI info line, score rationale) are truncated at the panel edge rather than wrapping. Information like the author, change counts, and CI status is silently invisible, and the meta/score boxes expand to fixed thirds of the column regardless of content, crowding the PR body. The overview also hides metadata the GitHub client already fetches (created/updated dates, requested reviewers, existing reviews) and lacks branch context entirely.

## What Changes

- **Wrap, don't clip**: metadata/title/score labels in the overview render with a bounded `width: 1fr` so long text wraps within the panel instead of overflowing off-screen.
- **Hugging boxes**: the meta and score containers stop expanding to fixed fractions of the overview column; they size to their content (`height: auto`), returning vertical space to the PR body.
- **Enriched metadata display**: the overview shows created date, updated-ago time, requested reviewers (capped with `+N more`), a compact existing-reviews summary line, and CI status with status-appropriate coloring.
- **Branch context**: the GitHub GraphQL query fetches the PR's base and head branch refs and the overview renders them (e.g. `base: main ← head: fix/ipfs-dedupe`).
- No breaking API/CLI/compat changes: `PullRequestData` gains two optional string fields; existing callers are unaffected.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `tui-review-client`: change the "Display selected PR overview and rationale" requirement so the overview renders full, wrapped metadata in content-hugging layout, and admits the enriched fields (created/updated dates, reviewers, existing-review summary, branch refs).
- `github-client`: change the "Fetch Pending Review Requests" requirement so the returned PR data additionally includes the base and head branch ref names.

## Impact

- `gitkeeper/github/queries.py`: add `baseRefName` and `headRefName` to the PR fragment in `REVIEW_REQUESTS_QUERY`.
- `gitkeeper/github/client.py`: add optional `base_ref` / `head_ref` fields to `PullRequestData` and parse them in `fetch_pending_review_requests`.
- `gitkeeper/ui/overview_view.py`: core reformat — CSS layout changes, stacked metadata rows, date/relative-time and reviewer-list helpers, CI color mapping.
- `tests/test_github_client.py`: mocked GraphQL fixtures updated with `baseRefName`/`headRefName`; assert parsed fields.
- `tests/test_ui.py`: coverage for wrapped rendering and metadata assertion (project has `pytest-textual-snapshot` for snapshot rendering).
- No new dependencies, no config changes, no API-version changes.