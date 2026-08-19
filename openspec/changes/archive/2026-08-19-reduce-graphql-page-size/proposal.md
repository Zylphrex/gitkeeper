## Why

The GraphQL query in `fetch_pending_review_requests` requests 100 PRs per page, each carrying nested review requests, reviews, and up to 100 touched-files entries. With many open review requests, a single page becomes so large that GitHub's API gateway returns `502 Bad Gateway`, failing the entire refresh and leaving the user with an empty queue. Users with a growing number of open PRs hit this frequently today.

## What Changes

- Reduce the GraphQL search page size from 100 to 25 PRs per request, so each page is roughly a quarter of its current weight and far less likely to trip the gateway's cost/time threshold.
- Add automatic retry with small exponential backoff (2 retries) on transient `5xx` responses (notably 502), so an occasional failing page can ride out the blip instead of aborting the whole refresh.
- Pagination to the complete result set is unchanged: the client still follows `pageInfo.endCursor` until `hasNextPage` is false (up to `MAX_RESULTS`). This is a behavior improvement, not a scope reduction.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `github-client`: The "Fetch Pending Review Requests" requirement changes in two ways — result pages are 25 pull requests per GraphQL query instead of 100, and transient 5xx responses are retried with backoff before failing.

## Impact

- `gitkeeper/github/queries.py` — `first: 100` → `first: 25` in `REVIEW_REQUESTS_QUERY`.
- `gitkeeper/github/client.py` — `PAGE_SIZE` constant (currently shared as 100) updated to 25; `_execute_query` (+ the REST diff fetch callsite, which shares the same request path pattern) gains bounded retry-with-backoff handling for 5xx responses.
- `tests/test_github_client.py` — existing pagination tests must still pass; add coverage for the smaller page size and for retry-then-succeed / retry-then-fail on 502.