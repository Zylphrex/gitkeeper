# Design — Sort PR Queue by Recent Activity

## Context

The current pipeline produces a band-first queue: `queue_sort_key` (`scoring/pipeline.py`) buckets items into active (ME_ACTIVE) vs waiting, orders active by tier→heat→size and waiting by wait-age, and the list view renders a separator + dimmed waiting section. Triage tiers (`TriageTier`, `assign_triage_tier`) are the only consumers of local git touch scores, hotness, and the T2-affinity gate; staleness markers and wait-age ordering exist only to decorate/order those two bands.

The new model (see `proposal.md`, and the delta specs) is a single flat queue ordered by `updated_at` (newest first), with every row badged by follow-up turn state. Most of the scoring machinery becomes dead and is removed; local git inspection survives only to power a "touched N/M files" chip in the overview.

## Goals / Non-Goals

**Goals:**
- One shared sort key: most recent activity (newest first), deterministic tie-break on repo then PR number.
- Every actionable row carries an action badge derived from `FollowUpState`; overview shows action-state line + reason chips.
- Remove tiers, staleness, waiting band, heat window, and affinity ranking from the product surface and from the scoring core.
- Keep `derive_followup_state` (the turn-state machine) and `is_actionable` gating unchanged.

**Non-Goals:**
- No change to GitHub fetching (`updated_at` is already fetched), to review submission, diff viewing, or keyboard navigation.
- No persistence/migration beyond config deprecation warnings.
- No new UI chrome beyond the badge/label replacement.

## Decisions

### D1 — Recency sort key lives in `scoring/pipeline.py`, exported for the list view
Introduce `activity_sort_key(item: ScoredPullRequest)` replacing `queue_sort_key`. It returns `(-timestamp, repo_name_with_owner, number)` ascending, where `timestamp` is parsed from `updated_at` (ISO-8601); unparseable/empty values sort as oldest. `updated_at` already comes from GitHub (`updatedAt`) and captures commits, comments, reviews, and state changes.

Alternatives considered: sorting on `pushed_at` (misses comment/review traffic), computing a composite recency score (over-engineering). `updated_at` matches the spec's "any activity" requirement.

`list_view.py` keeps re-sorting with the shared key so injected/mock scores follow the same order.

### D2 — Action badge derives from `FollowUpState`; rationale chips without tiers
`ME_ACTIVE` → `[awaiting you]` (bright style); `WAITING_AUTHOR` / `WAITING_OTHERS` → `[wait: author]` / `[wait: others]` (dim style). The badge strings live in a `list_view.py` mapping keyed by `FollowUpState`, mirroring the current `TIER_LABELS` pattern.

Column detail: the patience/time waiting-badge detail ("approved", "requested changes") comes from `_waiting_label` in the pipeline, which already produces reason text; it stays (computed for waiting items) and is appended to the dim badge. Awaiting rows show a compound `[awaiting you]` badge; the row-level reason chips remain in the overview, not the list rows.

### D3 — Actionable reasons survive as a tier-less reasons function
`assign_triage_tier` is deleted, but the reason chips it produced are still required by the overview spec. Replace it with a slim `derive_action_reasons(pr, touch_scores, username, heuristics) -> list[str]` computing only observable reasons:
- "you're the bottleneck" (all other direct-requested reviewers verdicted),
- "directly requested",
- "re-review due" (author pushed after my verdict),
- "respond to review" (I'm the author, external verdict landed after my push),
- "touched N/M files" (affinity → overview chip only).

It returns reasons and a rationale joining them, matching the existing `ScoreBreakdown.reasons` / `.rationale` shape so the overview keeps working. Dropped reasons from tier-era: "hot / author pushed recently" (heat window removed) and the generic "action" catch-all ("actionable").

### D4 — Config surface shrinkage + deprecation
In `FollowUpConfig`: remove `show_waiting_on_author`, `show_waiting_on_others`, `staleness_warn_after_days`. In `HeuristicsConfig`: remove `hot_window_hours`, `min_affinity_files`. While loading config, if any removed `followup.*` key appears in YAML, log a deprecation warning per key and ignore it (mirrors the existing `min_score_threshold` deprecation in `load_config`).

### D5 — Deletions across the codebase
- `scoring/calculator.py`: remove `TriageTier`, `assign_triage_tier`, `staleness_anchor_dt`, and `wait_age_hours`; keep `derive_followup_state` and helpers it needs (`_latest_my_review_dt`, `_latest_my_verdict`, `_re_review_due`, `derive_viewer_status`, etc.). Remove `ScoreBreakdown.tier`, `.stale_days`, `.wait_age_hours`; keep `follow_state`, `reasons`/`rationale`, `waiting_label`.
- `scoring/pipeline.py`: drop heat, staleness overlay, `hidden_by_config`, and the hot import; compute reasons for `ME_ACTIVE` and `waiting_label` for waiting; sort results with `activity_sort_key`.
- `git/decay.py`: no longer imported; tests updated. `git/inspector.py` stays (overview chip). `heuristics.lookback_days` remains in use by the chip.
- `ui/list_view.py`: drop `_band_start`, band separator rendering, `_pr_index`/`_option_index` offset math, tier mapping, and stale row text; add action-badge rendering and styles keyed by `FollowUpState`.
- `ui/overview_view.py`: remove `TIER_TITLES`, `TIER_COLORS`; show action-state line + `score.rationale`.
- `ui/app.py`: footer counts — keep "awaiting action vs waiting" counts, reworded.

### D6 — Band bookkeeping is deleted from `list_view`
With no separator row, `_band_start` and the one-index offset bookkeeping (`_pr_index`, `_option_index`) collapse to identity; filter-by-title and selection-preservation logic remain untouched (they already work on `ordered_prs`).

## Risks / Trade-offs

**[Degraded urgency for dormant awaiting-you PRs]** — recency sort buries an overdue PR that hasn't moved in 5 days even if the user is the only reviewer.
→ Mitigation: this is the intended model (label not position singles the turn of the day); the overview action-state line + reason chips still surface bottleneck/re-review when selected.

**[`updated_at` is bumped by your own actions]** — a PR you just moved as an awaited comment lands atop the queue on the next refresh (your action is "activity").
→ Mitigation: accepted per spec ("any activity"); the badge then shows `wait: author`/`wait: others` so the turn state stays readable.

**[Wide badges squeeze the 36-col row]** — `[awaiting you]` / `[wait: others]` consume metadata width already shared by repo + author.
→ Mitigation: the row budget reuses the existing truncation machinery (`_truncate`, `_effective_row_width`); repo truncates first, author truncates second, badge always fits.

**[Removed config keys in user YAML]** — existing config files may already set the removed keys.
→ Mitigation: deprecation warning on parse, keys ignored (no crash); tests cover the warning path.

## Migration Plan

1. Land the code deletion/refactor behind the current single pipeline; no schema or CLI surface changes outside the removals.
2. Update unit tests for new ordering, removed signals, and config deprecation.
3. No rollback path needed beyond reverting the single commit set.

## Open Questions

None that would change specs or tasks; deferred wording-only decisions (exact badge strings, colors) can be settled during implementation.