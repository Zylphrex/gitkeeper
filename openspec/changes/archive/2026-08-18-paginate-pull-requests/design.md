## Context

`GitHubGraphQLClient.fetch_pending_review_requests` (gitkeeper/github/client.py:97) runs `REVIEW_REQUESTS_QUERY` (gitkeeper/github/queries.py:3) exactly once and reads only `search.nodes`. The query uses `first: 50` with no `after` cursor and never requests `pageInfo`, so results are silently capped at one page. Every PR-review operation downstream (scoring, gates, TUI list) consumes whatever this one method returns, so the cap propagates as missing review items.

See proposal.md - Why for motivation. The behavior contract lives in specs/github-client/spec.md.

## Goals / Non-Goals

**Goals:**
- Return the complete set of matching open PRs regardless of count, once each.
- Stay within a single client method — no changes to callers' contract (`List[PullRequestData]` stays flat).
- Keep the existing single-batched-query-per-page efficiency.

**Non-Goals:**
- Paginating other connections (diff fetch, review mutations) — they are per-PR and already bounded.
- Adding offset/number-based pagination (GitHub search only supports cursor pagination).
- Async parallel page fetching — pages depend on the prior page's cursor.

## Decisions

### 1. Cursor-based pagination with `after` + `pageInfo`
Add a `cursor` variable to `REVIEW_REQUESTS_QUERY` passed as `after`, and request `search.pageInfo { hasNextPage endCursor }`. Loop in the client while `hasNextPage`, re-issuing with `after: endCursor`.

**Alternatives considered:**
- *REST search API with `page` param* — would require a new client path and a second API surface; rejects the established GraphQL path.
- *Only bumping `first` to 100* — cheaper but still a hard ceiling; rejected as the correctness problem (:50-person cap) is not a page-size problem.

### 2. Page size raised to 100
One page request `first: 100` to match GitHub's search-connection maximum, minimizing round trips. Pagination remains the guarantee; page size is only a constant.

### 3. Bound the loop with a safety valve
Cap total fetched nodes (e.g. 2000) and stop after detecting the cap is hit. Protects against runaway loops if GitHub ever returns a malformed `pageInfo`, without resuming the silent-truncation bug under normal conditions.

**Alternatives considered:** unbounded `while hasNextPage` — simplest, but a malformed response could loop; the cap degrades to the old behavior only in an exceptional case.

### 4. Dedup by node id
Results accumulate across pages; since search is cursor-based there should be no overlap, but dedup by `node["id"]` guards against API anomalies at negligible cost.

## Risks / Trade-offs

- [More API calls than today] → Bounded: page size 100 keeps a >50-PR backlog to at most a handful of pages; each page is one request.
- [GitHub's search API caps total results at 1000] → A user with >1000 requested reviews would still truncate; SDL triage, and the safety valve bounds behavior. Acceptable given the practical ceiling; no spec change planned.
- [`REVIEW_REQUESTS_QUERY` becoming callable with a cursor] → Parameter is optional in the GraphQL query; existing call sites (tests, other queries) unaffected until the loop is added.

## Migration Plan

Rollback is a revert of client.py and queries.py — the query gains an optional parameter, so there is no dual-version API contract. No data migration.

## Open Questions

None — the deferrable path is fully specified by specs/github-client/spec.md.