## Why

`fetch_pending_review_requests` issues a single GraphQL search with `first: 50` and never reads `pageInfo`. Reviewers with more than 50 open PRs awaiting their review silently lose the rest — and for a triage tool, "everything I owe review on" silently missing items is a correctness bug, not a performance nicety.

## What Changes

- Add cursor pagination to the pull-request search query (`pageInfo`/`endCursor`/`after`).
- Loop in `fetch_pending_review_requests` until all pages are fetched, deduplicating results across pages.
- Raise the per-page size to GitHub's search-connection maximum while keeping pagination as the correctness guarantee.
- No API contract change for callers: `fetch_pending_review_requests` still returns a flat `List[PullRequestData]`.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `github-client`: the "Fetch Pending Review Requests" requirement changes so the client returns the complete set of matching PRs regardless of count, not just the first page.

## Impact

- `gitkeeper/github/queries.py`: `REVIEW_REQUESTS_QUERY` gains a `pageInfo` block and a `cursor` variable for `after`.
- `gitkeeper/github/client.py`: `fetch_pending_review_requests` gets a fetch loop with a page-size ceiling and dedup.
- `tests/test_github_client.py`: extended to cover multi-page fetch and dedup.