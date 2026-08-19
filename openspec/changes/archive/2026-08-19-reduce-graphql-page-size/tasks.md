## 1. Reduce GraphQL page size

- [x] 1.1 Change `PAGE_SIZE = 100` to `PAGE_SIZE = 25` in `gitkeeper/github/client.py`
- [x] 1.2 Change the `search(... first: 100 ...)` literal to `first: 25` in `REVIEW_REQUESTS_QUERY` in `gitkeeper/github/queries.py`

## 2. Add bounded retry for 5xx responses

- [x] 2.1 Add a shared `_post_graphql`/`_get` retry wrapper to `client.py` that takes a `retries` parameter (default on), retries 5xx responses with a small exponential backoff (1s, then 2s), and re-raises on 4xx immediately (a 401 raises `PermissionError` without retry)
- [x] 2.2 Make `_execute_query` and `get_pull_request_diff` use the retry path (read requests retry 5xx up to 2 extra attempts)
- [x] 2.3 Pass `retries=False` from `add_pull_request_review` so mutations are never retried

## 3. Tests

- [x] 3.1 Add a test asserting `REVIEW_REQUESTS_QUERY` requests `first: 25` and that it matches the client's `PAGE_SIZE`
- [x] 3.2 Add a test that a page returning 502 twice then succeeding drives the client to return the expected results (3 total requests)
- [x] 3.3 Add a test that a hard-failing 502 after all retries raises the original HTTP error
- [x] 3.4 Add a test that auth failures (401) are not retried (fail immediately with `PermissionError`)
- [x] 3.5 Confirm all existing `tests/test_github_client.py` cases still pass and the full suite runs green