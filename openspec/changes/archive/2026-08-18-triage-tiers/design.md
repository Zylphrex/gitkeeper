## Context

The queue is currently sorted by a summed 0-100 composite score (`calculator.py`) where affinity (git touch buckets), assignment (direct/team), and urgency/size bonuses are added into one number. This blends two signals that should be separated: *who is waiting on me* (pressure) and *how well suited I am to review* (fit). Ties sort in GraphQL search order, and the `min_score_threshold` cutoff hides low-score PRs entirely. See proposal.md - Why.

Constraints shaping the redesign:

- The actionability gates (`is_actionable`) already produce the correct candidate set and must stay, with one carve-out added.
- Affinity signal (`PathTouchScore`, decay buckets) and the git inspector pipeline are reusable as-is.
- `min_score_threshold` is threaded through config, pipeline, app, list, and tests; removing it is a breaking surface change.
- The pull data already includes `reviewRequests`, `reviews[].submittedAt`, `updatedAt`, per-file sizes, and the latest commit's status check rollup.

## Goals / Non-Goals

**Goals:**

- Replace the composite score with a four-tier triage label (`T0/T1/T2/T3`).
- Enforce direct-request-above-team-ask precedence structurally, not via weights that can drift.
- Sort within a tier by author heat (hottest first), then review size, then deterministically.
- Make every actionable PR visible (no numeric cutoff).
- Provide granularity precise enough for "hot" and re-review detection without noise from comments or the user's own reviews.

**Non-Goals:**

- Learning/adaptation from review outcomes (direction D) — explicitly deferred.
- Fine-grained relevance weighting; tiers intentionally use coarse rules.
- Adding milestone/label signals — data surface is left as-is.
- Changing the diff viewer, submit-review flows, or navigation keys.

## Decisions

### Decision 1: Replace `ScoreBreakdown` with a tier assigner returning `TriageTier` + reason list

`calculate_relevance_score` becomes a tier assignment function. It consumes the same inputs (affinity signals, `requested_reviewers`, `reviews`, `updatedAt`, latest push timestamp, size) and returns a tier plus the reason chips that justify it. `total_score` disappears; the pipeline sorts on (tier, heat, size, then repo/number).

**Alternatives considered:**
- Keep the scalar but re-tune weights — rejected because direct/team precedence would degrade as weights drift and the "never place a team ask above a direct ask" rule stays implicit.
- Multiple orthogonal scores with a weighted combiner — more arbitrary parameters than we have signals.

### Decision 2: Tier assignment rules, evaluated top-down

```
T0 — Bottleneck: direct request AND every other requested reviewer already submitted a verdict
     (or the user is the only requested reviewer). CI not failing.
T1 — Hot/waiting: direct request to the user, OR author pushed within hot window,
     OR re-review due (user already verdict'd AND newer author push exists)
T2 — Team request with affinity: team-alias request AND the user has touched a
     minimum number of affected files (or the lone file, if single-file PR)
T3 — everything else actionable
```

Every PR lands in exactly one tier (first matching rule wins). Using first-match keeps the direct-above-team constraint structural instead of additive.

**Alternatives considered:**
- Additive compatibility max-from-scalar: requires keeping the old score which the proposal explicitly removes.

### Decision 3: Heat derives from a new `pushed_at` field on the PR, not `updatedAt`

The GraphQL commit connection already fetches the latest commit. Its `committedDate` is populated on PR head commits (unlike `pushedDate`, which GitHub only fills on default branches). This single timestamp powers the re-review carve-out in the gate and the heat signal, and unlike `updatedAt` it does not move on comments and the user's own review submission.

**Trade-off:** one extra query field (already batched; negligible cost) for correctness in the "hot" signal. Alternative (derive from `updatedAt`) avoided because a user's own action would "heat up" a PR they just reviewed.

### Decision 4: The gate's already-reviewed rule becomes a carve-out

The current "already reviewed" exclusion (`gates.py`) stays for genuinely stale PRs *when nothing happened since my verdict*. If `pushed_at > my latest review.submitted_at`, the PR re-enters the queue as a re-review item instead of being dropped.

### Decision 5: Config knobs supersede `min_score_threshold`

`min_score_threshold` is removed. New knobs in the `heuristics` block:

- `hot_window_hours` (default 6): fresh push → T1 heat.
- `min_affinity_files` (default 1): changes to go from T3 to T2 or within-tier.
- (optional) `tier_grouping`: whether T3 renders dimmed or fully; default fully visible.

Removal is a breaking config change. Existing `min_score_threshold` keys in user configs will silently be ignored (pydantic keeps unknown keys) — the tool should log a deprecation warning when present and remove the key.

**Alternative considered:** keep threshold as a "collapse below T3" preference — rejected per decision from exploration: no hiding; labels + sort only.

## Risks / Trade-offs

- **Heat via `committedDate` requires a GraphQL payload change** → Mitigation: it's one field, additive, on existing `commits` connection; client parsing has a test and was verified against a live token.
- **Tier granularity may feel coarse** — two PRs in the same tier may look equal in the list. → Mitigation: within-tier secondary keys (heat, size, deterministic repo/number) are visible, and reason chips tell the tie-breaker story.
- **Bottleneck detection depends on verdict accuracy** — a review-request answered by a team alias might count as a peer verdict when that team actually contains the user. → Mitigation: treat team-alias requested reviewers as "other" so user believes their own verdict; flag false bootstrap in tests with aliased reviewers.
- **Deprecation of `min_score_threshold` breaks stores of user configs.** → Mitigation: document the change in proposal/release notes; ignore extra key with warning log instead of hard failure.

## Migration Plan

1. Land the GitHub/query/parse change first (adds `pushedAt`), covered by client tests — safe, doesn't affect scoring.
2. Replace scoring in a second commit: new tier function + pipelining + config knobs; remove `min_score_threshold` (log-warn if present).
3. UI switch in the same commit as scoring (list label + overview breakdown), so the tree is never mid-migration.
4. Tests updated to the new API; the old scalar comparisons in `test_scoring.py`/`test_ui.py` removed or converted proportionally.

Rollback: revert the scoring commit; the UI overlay that removed it also reverts with it. No data migration needed in user config persistence.

## Open Questions

- Exact values for `hot_window_hours` and `min_affinity_files` — defaults are fine; tune later when real data exists.
- Whether later tier boundaries can be derived from review outcomes — not now; the triage format supports adding it without changing the tier model.