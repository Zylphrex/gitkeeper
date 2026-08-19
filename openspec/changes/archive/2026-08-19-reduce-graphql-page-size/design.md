## Context

See proposal.md — Why. Current state: `fetch_pending_review_requests` paginates the GraphQL `search` connection with `PAGE_SIZE = 100` (client.py:64) hardcoded as `first: 100` in `REVIEW_REQUESTS_QUERY` (queries.py:5). Each page nests `reviewRequests(first:20)`, `reviews(first:30)`, and `files(first:100)` per PR, so a full page can carry tens of thousands of nodes and trip GitHub's gateway into returning 502. A 502 anywhere in the loop aborts the whole refresh (all-or-nothing). Retry semantics do not exist today; `_execute_query` calls `raise_for_status()` immediately.

Scope of retry: only the **read path** — the paginated search loop and the diff GET. Review submissions (mutations) are excluded from retries because retrying a mutation that the server may have already accepted risks double-applying a review.

## Goals / Non-Goals

**Goals:**
- Make each GraphQL page small enough to fit under GitHub's gateway cost/time threshold reliably.
- Survive transient 5xx blips with bounded retry + exponential backoff.
- Preserve complete-result pagination, dedup across pages, and `MAX_RESULTS` behavior.

**Non-Goals:**
- Shrinking per-PR nested caps (`files`/`reviews`/`reviewRequests`) — deliberately deferred; the page-size reduction is the primary weight lever.
- Changing `MAX_RESULTS` or the total number of requests (2000 results now costs up to 80 requests at page 25 — see Risks).
- Partial-result UI (degrade-and-show-some on a failed page). Out of scope; all-or-nothing error behavior stays.
- Retrying mutations.

## Decisions

**1. Outer page size 25, driven by `PAGE_SIZE` constant.**
`PAGE_SIZE = 25` in the client and `first: 25` in `REVIEW_REQUESTS_QUERY`. The GraphQL `first` literal is checked at archive/validate by static audit — keeping it and `PAGE_SIZE` in lockstep matters. A 25-page tips the per-page worst-case from ~15,000 to ~3,750 nested nodes, comfortably below the observed failing range. Alternatives considered: 50 (only 2× weight cut, lighter relief), 10 (4× request fan-out at the top but within `MAX_RESULTS` budget; more cumulative requests with 2000 open PRs).

**2. Bounded retry in the read path with `httpx` + pass-safe design.**
Wrap the HTTP call in a `_execute_query(..., retries: bool = True)`-style helper parameterized at callsite:
- Read calls (`_execute_query` for search/viewer, `get_pull_request_diff`) pass `retries=True` → 2 attempts.
- `add_pull_request_review` passes `retries=False` (no retry on mutation).
- Retry only on HTTP 5xx (any value) — never on 4xx (a 401 remains an immediate `PermissionError`), and not on GraphQL-level `errors` in a 200 body.
- Backoff schedule: attempt → 1s, then 2s (fixed small exponential), because refresh/diff runs live in a background thread (`@work(thread=True)`) and the UI is not blocked.
- Implementation detail: per-attempt timeouts are unchanged (15s GraphQL, 30s REST).

Alternatives considered:
- External retry via `httpx` Transport/Mount transports — cleaner separation but introduces a second mechanism; inlining is a ~20-line delta and keeps the auth branch (`401`) explicit.
- `tenacity` dependency — overkill for one bounded loop; avoid new deps.
- Retry at app level (UI `action_refresh_queue`) — works only for whole-refresh retry, not per-page; retrying the loop from page 1 is more disruptive than retrying just the failed page.

## Risks / Trade-offs

- [More requests: 2000-open-PR snapshot → up to 80 sequential pages] → Acceptable in practice; actual mailboxes rarely approach 2000. If it surfaces, reduce `MAX_RESULTS` in a follow-up change.
- [Retry does not eliminate large 502s — only jitter] → Mitigated by item 1 (smaller page) which addresses deterministic weight; retry addresses flaky ones. Both are in this change.
- [No partial results if a page hard-fails] → Stays al-or-nothing; documented as out of scope. If a hard 502 persists after retries, the refresh fails uniformly as today, just less often.
- [Slower cold-queue with large sets] → Small pages add request fan-out; each is much faster to serve. Net wall-clock usually improves because the earlier pages were timing out.

## Migration Plan

Revert-safe: change is localized to `queries.py` + `client.py`. Rollback = revert `PAGE_SIZE`/`first` and remove the retry wrapper; no schema/data migration, no config surface added.

## Open Questions

None — decisions locked with the user (page size 25, no nested-cap trimming, 2× retry with backoff).