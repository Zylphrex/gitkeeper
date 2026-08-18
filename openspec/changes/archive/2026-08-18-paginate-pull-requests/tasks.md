## 1. Query changes

- [x] 1.1 Add a `$cursor: String` variable and `after: $cursor` argument to the `search` connection in `REVIEW_REQUESTS_QUERY` (gitkeeper/github/queries.py)
- [x] 1.2 Add a `pageInfo { hasNextPage endCursor }` block under `search` in `REVIEW_REQUESTS_QUERY`
- [x] 1.3 Bump the per-page `first: 50` to `first: 100`

## 2. Client pagination loop

- [x] 2.1 Define a page constant (e.g. `PAGE_SIZE = 100`) and a total-nodes safety cap (e.g. `MAX_RESULTS = 2000`) in gitkeeper/github/client.py
- [x] 2.2 Refactor `fetch_pending_review_requests` to loop: execute the query, append nodes, and re-issue with `after: cursor` while `hasNextPage` and the safety cap is not reached
- [x] 2.3 Deduplicate accumulated results by PR node id before mapping to `PullRequestData`
- [x] 2.4 Keep the existing single-page node-parsing block intact (no behavior change to field extraction)

## 3. Tests

- [x] 3.1 Extend tests/test_github_client.py to verify `after` cursors and `pageInfo` are read from the query response
- [x] 3.2 Add a test asserting results across multiple pages (mock server returning `hasNextPage: true` then `false`) are all returned
- [x] 3.3 Add a test asserting duplicate node ids across pages are returned only once
- [x] 3.4 Add a test asserting the loop stops when `hasNextPage` is `false`

## 4. Verification

- [x] 4.1 Run the full test suite (e.g. `pytest`) and confirm green