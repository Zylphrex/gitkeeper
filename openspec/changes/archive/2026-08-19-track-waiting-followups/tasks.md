## 1. Configuration

- [x] 1.1 Add `FollowUpConfig` (pydantic) with `include_authored`, `show_waiting_on_author`, `show_waiting_on_others` (all default `true`) and `staleness_warn_after_days` (default `3`) on a new `followup` field of `Config` in `gitkeeper/config.py`
- [x] 1.2 Confirm `load_config` resolves the `followup` block with the above defaults and that no existing module regresses when the key is absent

## 2. GitHub client fetch

- [x] 2.1 Keep `REVIEW_REQUESTS_QUERY` unchanged for the request-timestamp: GitHub's `ReviewRequest` type exposes no `createdAt`, so staleness for the no-verdict case anchors on the PR's `createdAt`
- [x] 2.2 Confirm the requested-reviewer model in `gitkeeper/github/client.py` requires no per-request timestamp (the schema rejects `createdAt` on `ReviewRequest`)
- [x] 2.3 Fetch authored PRs: update `fetch_pending_review_requests` to merge a second search `is:open is:pr author:@me archived:false` (per-user equivalent where `author:` needs a login) into the same page loop, reusing `seen_ids` de-dupe, page size, and 5xx retry behavior

## 3. Scoring: follow-up turn state

- [x] 3.1 Add a `FollowUpState` enum (`ME_ACTIVE`, `WAITING_AUTHOR`, `WAITING_OTHERS`) in `gitkeeper/scoring/calculator.py`
- [x] 3.2 Implement `derive_followup_state(...)` computing the turn from relationship, my latest verdict, external verdicts, and `pushed_at`: requested-no-verdict → active; my verdict + author push after → active (re-review); my verdict `CHANGES_REQUESTED` no push → waiting on author; my verdict `APPROVED`/`DISMISSED` no push → waiting on others; authored + external verdict after my push → active (respond to review); authored idle → waiting on others
- [x] 3.3 Add the authored-response rule to `assign_triage_tier`: authored + fresh external verdict → `T1` with reason `"respond to review"`, first-match-wise below the bottleneck rule and above the T2 team-affinity branch
- [x] 3.4 Add the staleness marker (`stale_days: Optional[int]`) to `ScoreBreakdown`, computed per state: requested-no-verdict ages from the PR `createdAt` (no request timestamp exists in the schema); re-review / respond-to-review age from the author's latest push; omit when no anchor timestamp parses

## 4. Pipeline and queue ordering

- [x] 4.1 In `gitkeeper/scoring/pipeline.py`, assign `FollowUpState` for every gated-open PR, apply the `show_waiting_on_*` config to drop the corresponding waiting items from the output, and never let a waiting item be discarded via a score threshold
- [x] 4.2 Update `queue_sort_key` / the waiting-band tie-break so ALL active items order before every waiting item, and waiting items sort by age of the user's most recent act (oldest first) then deterministically by repo and number

## 5. Terminal interface

- [x] 5.1 In `gitkeeper/ui/list_view.py`, render active entries first in the existing format, then a dimmed section separator, then the waiting-band rows labeled with their reason (waiting on author / awaiting reviewers / approved), keeping the whole region one scrollable, selectable list
- [x] 5.2 Render the staleness marker (`N d`) in the active-band metadata row only for entries whose `stale_days` exceeds `followup.staleness_warn_after_days`, respecting the existing per-row width budget so rows never wrap
- [x] 5.3 In `gitkeeper/ui/app.py`, classify each scored PR's band once after scoring and pass band plus staleness into the option list; ensure a waiting-band selection still drives the overview pane
- [x] 5.4 When both `show_waiting_*` flags are false, suppress the band and its separator entirely (queue renders as today)

## 6. Tests

- [x] 6.1 Unit tests in `tests/test_scoring.py` for every turn-state scenario in the relevance-scoring delta spec (requested-no-verdict, re-review, waiting-on-author, waiting-on-others, authored with fresh feedback)
- [x] 6.2 Unit tests in `tests/test_scoring.py` for the authored-response T1 tier rule with mixed direct/team/heat inputs
- [x] 6.3 Unit tests for staleness marker computation (anchor selection and threshold flagging)
- [x] 6.4 Unit tests for `FollowUpConfig` parsing, defaults, and fallback in the existing config test module
- [x] 6.5 Unit tests for `fetch_pending_review_requests` merging both searches and de-duping on id, plus a 502 retry case for the authored query
- [x] 6.6 Unit tests that active items always sort before waiting items and waiting items order oldest-first