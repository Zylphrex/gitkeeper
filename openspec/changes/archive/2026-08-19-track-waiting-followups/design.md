## Context

See proposal.md — Why. The pipeline today fetches review-requested PRs, hard-gates them (`scoring/gates.py:is_actionable`), and runs T0–T3 tiering (`scoring/calculator.py:assign_triage_tier`). It already fetches the raw timestamps needed for a turn model: `reviews { author, state, submittedAt }` and the latest commit push time (`pushed_at`), and the TUI renders a single ordered queue with no notion of a waiting state — submitted reviews vanish unless the author pushes again.

## Goals / Non-Goals

**Goals:**
- Derive a per-PR follow-up turn state (`ME_ACTIVE` / `WAITING_AUTHOR` / `WAITING_OTHERS`) statelessly, from the already-batched payload.
- Add exactly one authored fetch source (`author:@me`) that reuses the existing search payload, pagination, and retry path.
- Split the queue into an active band (tiered) and an always-visible dimmed waiting band, both served by one pipeline pass.
- Mark stale `ME_ACTIVE` follow-ups ("outstanding N days") as a display flag, never a filter.
- Add a `followup` config block, on by default, with per-band toggles.

**Non-Goals:**
- No thread/comment-reply detection: a reply without an author push does not re-trigger a review turn (cheap B-i).
- No `commenter:@me` search surface — only `review-requested:@me` plus `author:@me`.
- No local state or seen-markers; turn states are recomputed every refresh (stateless by design).
- No snooze / dismiss / archive actions.

## Decisions

### Every turn state is derived, nothing is stored
A `FollowUpState` enum is computed in the scoring pipeline from data already fetched: relationship (`author == me`, requested directly, requested via team), my latest verdict by timestamp, external reviewer verdicts, and `pushed_at`. The derivation extends the existing re-review logic (`_re_review_due`, verdict comparisons) symmetrically:
- requested, no verdict → `ME_ACTIVE`
- my verdict + author push after → `ME_ACTIVE` (`re-review`)
- my verdict `CHANGES_REQUESTED`, no push after → `WAITING_AUTHOR`
- my verdict `APPROVED`/`DISMISSED`, no push after → `WAITING_OTHERS`
- authored, external verdict after my latest push → `ME_ACTIVE` (`respond to review`)
- authored, nothing after my push → `WAITING_OTHERS` (awaiting reviewers)

Rationale: the alternative (caching session state) demands persistence the tool does not have; timestamp comparisons stay cheap and correct on every run.

### Waiting band emerges from classification, not a second query
The waiting band is the set of open PRs that pass the hard gates (draft/CI/closed) but classify `WAITING_*`. `ignore_failing_ci` continues to exclude failing-CI items from every band. When a band's `show_*` config flag is false, those items are simply dropped before sorting, reproducing today's post-review behavior for that band alone.

### One payload, two search terms, de-duped on id
`REVIEW_REQUESTS_QUERY` is reused for both `review-requested:@me` and `author:@me`; results merge under the existing `seen_ids` de-dup. GitHub's GraphQL `ReviewRequest` type exposes no timestamp, so an exact "requested since" is unavailable; staleness for the no-verdict case clocks from the PR `createdAt` instead. The authored node already exposes `author { login }`.

### Authored-response items rank at T1
A new first-match rule in `assign_triage_tier` — authored + external verdict after my latest push → `T1`, reason `"respond to review"` — sits below the bottleneck (T0) and direct/hot/re-review (T1) rules and above the T2 team-affinity branch, keeping "reply to a review on my PR" above team asks in the list ordering.

### Staleness is a display marker computed at score time
`ScoreBreakdown` gains a `stale_days: Optional[int]` field with the staleness age anchored per case:
- requested review, no verdict: age since PR `createdAt` (no request timestamp exists on GitHub's `ReviewRequest`)
- re-review due: age since the author's latest push
- respond-to-review: age since the user's latest push

When no anchor timestamp parses, the marker is omitted (never a filter, never an approximate guess).

### Sort: active band keeps the current sort key
The active band reuses `queue_sort_key` unchanged (tier → heat → size → deterministic). `ME_ACTIVE` authored-response items enter the band via their T1 tier. Waiting items are sorted by age of the user's last act (oldest first), then deterministically, and are always placed after all active items.

### Config surface
`FollowUpConfig` on `Config.followup`:

```yaml
followup:
  include_authored: true        # fetch author:@me PRs
  show_waiting_on_author: true  # CHANGES_REQUESTED, no push back
  show_waiting_on_others: true  # my PR awaiting reviews / approved & idle
  staleness_warn_after_days: 3  # flag active items beyond this
```

`load_config` wires a default-filled `FollowUpConfig`; `pipeline.process` passes it through alongside the existing `heuristics`.

### TUI rendering
`list_view.py` renders a single vertical scroll region: tiered active entries first (existing two-row format), then a dimmed section separator and the waiting band rows (repo + number + reason, plus `staleness days`). The waiting band remains selectable for the overview panel. `app.py` recomputes which row belongs to which band once after scoring rather than per-frame.

## Risks / Trade-offs

- [Longer queue — authored PRs with no fresh feedback also appear] → dim + trailing placement; `include_authored` / `show_waiting_*` off-switches restore today's behavior.
- [Slower refresh: extra field + authored page] → same 25/page cap and retry wrapper; both searches share one node shape and dedupe on id.
- [Author reply without a push stays invisible] → accepted ceiling (B); a later upgrade can add thread timestamps to the batch payload.
- [No request timestamp on `ReviewRequest` (createdAt rejected by the schema)] → staleness for the no-verdict case uses PR `createdAt`, the only available clock.

## Open Questions

None — the remaining unknowns (exact row styling, marker format) are presentation details the implementer can settle without changing specs, design, or task breakdown.