# Sort PR Queue by Recent Activity

## Why

The current queue is sorted by an opinionated triage model — band-first (activate-vs-waiting), then tier (T0–T3), then heat, then diff size — and renders the waiting band as a separate dimmed section. That stack of heuristics is hard to reason about: position implies urgency, but the rules behind it ("you're the bottleneck", "hot window", "team affinity") are a moving target. The user wants a transparent mental model: *the queue is ordered by whatever most recently moved, and every row says whose turn it is.* No tiers to trust, no hidden band cut, no staleness decorations to decode.

## What Changes

- **Sort by most recent activity** (`updated_at`, newest first) across all actionable PRs, deterministic tie-break on repo and number. Replaces tier→heat→size within bands, and the waiting band's own "oldest wait first" ordering.
- **Single flat list** — no active/waiting band separation, no separator row. Waiting-on-author and waiting-on-others PRs stay interleaved by recency with the review-requested ones.
- **Label every row with whose turn** — awaiting-you rows get a bright badge (`[awaiting you]` + reason detail); waiting rows get a dim `[wait: author]` / `[wait: others]` badge. The label, not the position, carries the "action is on me" signal.
- **Remove the T0–T3 triage tiers entirely** — no tier badge in the list, no tier title in the overview at the end of the pipeline: `TriageTier`, `assign_triage_tier`, tier labels/colors, and the `triage-tiers` capability are deleted.
- **Remove the staleness `[Nd]` marker** and the `staleness_warn_after_days` setting.
- **Remove the waiting-band display settings** — `show_waiting_on_author` / `show_waiting_on_others` no longer hide PRs; all actionable PRs show, labeled.
- **Demote local git affinity to overview-only context** — touched-files still inspected and surfaced as a "why this is yours" chip in the overview, but it never ranks or orders anything.
- **Remove dead heuristic config** — `hot_window_hours` (heat only fed tier) and `min_affinity_files` (only gated T2) are removed along with `staleness_warn_after_days`.

## Capabilities

### New Capabilities
<!-- none -->
- (none — the ordering and labeling model is expressed by modifying existing capabilities)

### Modified Capabilities
- `relevance-scoring`: turn-state classification stays; "Flag Stale Follow-ups" is removed; "Calculate Affinity and Urgency Size" is replaced by an overview-contexts affinity requirement plus a new recency-ordering requirement; "Actionability Gating" wording stops referring to bands.
- `triage-tiers`: **REMOVED entirely** — tier assignment, tier ordering, the tier-ordered queue, authored-triage, and the separate waiting-band ordering requirements are all deleted.
- `tui-review-client`: the queue list sorts by recency instead of tier; rows render awaiting-action badges instead of tier labels; the waiting band and its separator are removed; the overview drops tier title (keeps rationale chips); staleness row marker is removed.
- `config-management`: the follow-up schema drops waiting-band and staleness options; only `include_authored` remains in the `followup` block.

## Impact

- `gitkeeper/scoring/calculator.py` — delete `TriageTier`, `assign_triage_tier`, staleness helpers; keep follow-up turn state machine.
- `gitkeeper/scoring/pipeline.py` — replace `queue_sort_key` with a recency key; drop sorting/banding/staleness wiring.
- `gitkeeper/git/inspector.py` — retained unchanged; output feeds an overview "touched N/M files" chip only.
- `gitkeeper/ui/list_view.py` — flat list, awaiting badges, drop band separator and tier/stale rendering; index mapping simplifies.
- `gitkeeper/ui/overview_view.py` — drop `TIER_TITLES`/tier title; show follow-up state + rationale chips.
- `gitkeeper/ui/app.py` — status-line percent counts ("awaiting you" vs "waiting") updated.
- `gitkeeper/config.py` — drop `hot_window_hours`, `min_affinity_files`, `show_waiting_on_author`, `show_waiting_on_others`, `staleness_warn_after_days`.
- tests: `test_scoring.py`, `test_ui.py`, `test_config.py` updated for the new ordering and removal axis.