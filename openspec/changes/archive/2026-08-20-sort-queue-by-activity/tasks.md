# Tasks — Sort PR Queue by Recent Activity

## 1. Scoring Core Refactor

- [x] 1.1 Remove `TriageTier`, `assign_triage_tier`, `staleness_anchor_dt`, and `wait_age_hours` from `gitkeeper/scoring/calculator.py`; retain `derive_followup_state` and its dependencies
- [x] 1.2 Remove `tier`, `stale_days`, and `wait_age_hours` fields from `ScoreBreakdown` in `gitkeeper/scoring/calculator.py`
- [x] 1.3 Add tier-less `derive_action_reasons(pr, touch_scores, username, heuristics)` returning reason strings and rationale (bottleneck, directly requested, re-review due, respond to review, touched N/M files)
- [x] 1.4 Replace `queue_sort_key` with `activity_sort_key` in `gitkeeper/scoring/pipeline.py` sorting by `-updated_at` timestamp (newest first), tie-break repo then number; unparseable timestamps sort oldest
- [x] 1.5 Rewire `RelevancePipeline.process` in `gitkeeper/scoring/pipeline.py`: drop heat, staleness overlay, `hidden_by_config`, and tier calls; set reasons for `ME_ACTIVE`, `waiting_label` for waiting items; sort with `activity_sort_key`
- [x] 1.6 Remove now-unused imports and the `WAITING_LABELS`/`_waiting_label` handling that is no longer reachable (keep `_waiting_label` if still consumed)
- [x] 1.7 Delete `gitkeeper/git/decay.py` (compute_decay_score_for_touches), keeping `gitkeeper/git/inspector.py` for the overview chip

## 2. UI — Flat Recency-Ordered List

- [x] 2.1 In `gitkeeper/ui/list_view.py`, add `ACTION_BADGES` mapping `FollowUpState` to `(badge_text, style)` for `awaiting you`, `wait: author`, `wait: others`
- [x] 2.2 Drop tier and staleness rendering (`_tier_style`, TIER_LABELS, stale badge) and the `waiting` band separator build-up (`_band_start`), and flatten the band index math (`_pr_index`/`_option_index`)
- [x] 2.3 Update `_populate_list` to render the action badge plus number, repo, and author on each metadata row
- [x] 2.4 Remove `waiting_prs` band tracking and the wait-band related attribute from `PRListView`
- [x] 2.5 In `gitkeeper/ui/overview_view.py`: delete `TIER_TITLES`/`TIER_COLORS` and show an action-state line plus `score.rationale`
- [x] 2.6 In `gitkeeper/ui/app.py`: reword footer/status counts to "awaiting you" vs "waiting" and drop any tier-count references

## 3. Config

- [x] 3.1 In `gitkeeper/config.py`: remove `show_waiting_on_author`, `show_waiting_on_others`, and `staleness_warn_after_days` from `FollowUpConfig`
- [x] 3.2 Remove `hot_window_hours` and `min_affinity_files` from `HeuristicsConfig`
- [x] 3.3 In `load_config`, log a deprecation warning (ignoring) any removed `followup.*` key present in YAML, mirroring the `min_score_threshold` handling

## 4. Tests

- [x] 4.1 Update `tests/test_scoring.py`: remove tier-assignment tests; replace queue-ordering tests with activity ordering (newest first, deterministic tie-break); drop staleness/wait-age tests
- [x] 4.2 Update `tests/test_ui.py`: assert `awaiting_you`/`wait` badges, no separator row, no tier/stale text; repair selection-preservation assertions for flat-list offsets
- [x] 4.3 Update `tests/test_config.py`: remove `hot_window_hours` fixture, cover `followup.*` deprecation warnings for removed keys
- [x] 4.4 Update `tests/test_git_inspector.py`: drop imports of the removed decay module; keep `inspect_path_touches` assertions

## 5. Verification

- [x] 5.1 Run the full test suite (`pytest`) and fix any regressions
- [x] 5.2 Grep for residual tier/staleness/waiting-band identifiers (`TriageTier`, `tier`, `stale_days`, `waiting band`, `hot_window`, `queue_sort_key`) and remove or dead-end the rest
- [x] 5.3 Sanity-check the TUI manually (queue orders by updated activity, badges render on each row, the band separator is gone)