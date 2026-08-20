## Context

See proposal.md — Why. The pipeline fetches `review-requested:@me` plus `author:@me` through `REVIEW_REQUESTS_QUERY` (`gitkeeper/github/client.py:fetch_pending_review_requests`), merges pages on `seen_ids`, hard-gates (`scoring/gates.py`), classifies each into a turn state (`scoring/calculator.py:derive_followup_state`), and renders one flat activity-sorted queue with `●/◇/○` badges (`ui/list_view.py`). GitHub de-lists the user from `requestedReviewers` the moment they submit a review, so `review-requested:@me` stops matching — an approved-then-idle PR disappears even though it is open. That is why the `WAITING_OTHERS` "approved" path in the classifier has only ever been reachable for PRs the user authored.

The follow-up classifier and queue already encode everything needed for the new states; only the fetch surface and two classifier edges are wrong.

## Goals / Non-Goals

**Goals:**
- Keep open pull requests the user reviewed (approve/request-changes/comment) visible in the queue until they merge, by adding a `reviewed-by:@me` fetch source that reuses the existing search payload, page size, retry, and id de-dup.
- Fix the authored-PR mislabel so an external **approval** shows as waiting to merge, not "respond to review".
- Gate the wider surface behind a default-on `followup.include_reviewed` toggle.
- Zero TUI rendering changes: the flat queue, `●/◇/○` badges, and status-bar counts already represent the three states.

**Non-Goals:**
- No `commenter:@me` surface (matches any comment); `reviewed-by:@me` is the targeted reviewer-participation qualifier. This intentionally revises the `track-waiting-followups` non-goal that limited surfaces to `review-requested` + `author`.
- No local state or seen-markers; turn states stay derived, recomputed every refresh.
- No snooze/dismiss/merge actions; visibility is the deliverable.

## Decisions

### Third search source, merged on id — `reviewed-by:@me`
`fetch_pending_review_requests` gains an `include_reviewed` flag; when on, it issues `is:open is:pr reviewed-by:@me archived:false` through the same `extend_search` path, so pagination, retry, and `seen_ids` de-duplication apply unchanged. `reviewed-by:@me` matches PRs where the user has an authored review (any state: APPROVED / CHANGES_REQUESTED / comments), and crucially continues to match after the user is de-listed as a requested reviewer.

Alternatives considered:
- *`commenter:@me`* — matches casual comments on top of formal reviews; too broad, adds noise the classifier has no good home for.
- *Persist a local "reviewed PR ids" store* — reintroduces session state and staleness the codebase deliberately avoids (recompute-every-refresh design).

### `followup.include_reviewed`, default true
`FollowupConfig` gains `include_reviewed: bool = True`, mirroring `include_authored`; `pipeline`/`app` pass it to the fetch. Off restores today's behavior exactly. Alternative (always-on, no toggle) rejected: high-volume reviewers need an off-switch for the extra page traffic and queue length without editing queries.

### Respond-to-review only for verdicts that demand a response
The authored branch in `derive_followup_state` (and the matching guard in `derive_action_reasons`) keys `ME_ACTIVE` "respond to review" off *any* external verdict after the latest push. Change it to key off the **latest external verdict**: if it is `CHANGES_REQUESTED` (the one verdict demanding an author response) and after the user's latest push → `ME_ACTIVE`; otherwise (latest is APPROVED or nothing actionable) → `WAITING_OTHERS`.

Rationale: an approval carries no ball; "respond to review" should never be triggered by a thumbs-up. Basing it on the latest overall verdict keeps the outcome stable as approvals follow change requests.

### Waiting label: authored-but-approved renders "approved"
`pipeline.py:_waiting_label` currently returns "awaiting reviewers" for any authored `WAITING_OTHERS` item, which would mislabel an externally-approved PR of the user. Extend it so an authored `WAITING_OTHERS` item with a latest external verdict of APPROVED renders "approved" (i.e., waiting to merge), and only renders "awaiting reviewers" when no reviewer has acted.

### Reviewed PRs reuse the existing re-review path
A user-reviewed, non-authored PR where the author later pushes already classifies `ME_ACTIVE` (re-review) via the existing `pushed > my_verdict` branch; it just never had data before. No new branch.

### TUI is untouched
The queue is already a single flat list with per-row `●/◇/○` badges and interleaved activity ordering (`relevance-scoring` "Order Queue by Recent Activity" + `tui-review-client` "Interactive PR Queue Navigation"). Re-surfaced items render with existing styles, so `ui/` needs no edits. Status-bar counts in `app.py` naturally reflect the wider set.

## Risks / Trade-offs

- [Queue grows: all open PRs the user ever reviewed now surface] → already sorted by recency, resting items drop below newer activity; `include_reviewed: false` is the full restore switch.
- [`reviewed-by:@me` may include PRs where the user only commented, not formally reviewed] → the classifier still routes them sensibly (re-review after push, waiting otherwise); visibility is the point of this change.
- [Verdict ordering edge: CHANGES_REQUESTED then later APPROVED] → resolving on the latest external verdict prevents flicker; the classifier never oscillates within a refresh.
- [Slower refresh: a third search executes] → same 25/page cap, shared retry wrapper, and id de-dup; the named per-search costs are bounded and identical to the existing authored search.

## Migration Plan

Config-only additive change: `include_reviewed` defaults on with no migration. Rollback for any deployment is `followup.include_reviewed: false` in config — no code revert required.

## Open Questions

None — the remaining unknowns (exact wording of the "approved" waiting label, badge reuse) are presentation details resolvable during implementation without changing specs, design, or tasks.
