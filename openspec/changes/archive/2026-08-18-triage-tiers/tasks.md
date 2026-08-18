## 1. GitHub Client: Latest Push Timestamp

- [x] 1.1 Add `committedDate` to the final `commits.last(1) { nodes { commit { } } }` selection in `gitkeeper/github/queries.py` (alongside `statusCheckRollup`; `pushedDate` is null for PR head commits)
- [x] 1.2 Add `pushed_at: Optional[str]` field to `PullRequestData` in `gitkeeper/github/client.py`
- [x] 1.3 Parse `committedDate` from the latest commit node in `fetch_pending_review_requests` and populate `pushed_at`
- [x] 1.4 Add/new test asserting the client parses `committedDate` into `PullRequestData.pushed_at`

## 2. Config: New Heuristics Knobs

- [x] 2.1 Remove `min_score_threshold` from `HeuristicsConfig` in `gitkeeper/config.py`
- [x] 2.2 Add `hot_window_hours: int = Field(default=6, ...)` to `HeuristicsConfig`
- [x] 2.3 Add `min_affinity_files: int = Field(default=1, ...)` to `HeuristicsConfig`
- [x] 2.4 Add a deprecation warning (log.warning) in `load_config` when a parsed config still contains `min_score_threshold`
- [x] 2.5 Update `tests/test_config.py` to drop `min_score_threshold` assertions and cover the new knobs

## 3. Scoring: Replace Composite with `TriageTier`

- [x] 3.1 Add a `TriageTier` enum (`T0`, `T1`, `T2`, `T3`) with order weights in `gitkeeper/scoring/calculator.py`
- [x] 3.2 Replace `ScoreBreakdown.total_score` with `tier: TriageTier` while keeping `rationale` and `reasons`
- [x] 3.3 Rename `calculate_relevance_score` to a tier assigner (e.g. `assign_triage_tier`) consuming `pushed_at` in addition to existing inputs
- [x] 3.4 Implement first-match tier rules:
  - `T0`: direct request AND (all other requested reviewers have a verdict OR user is the only requested reviewer) AND CI not failing
  - `T1`: direct request, OR author push within `hot_window_hours`, OR re-review due (user verdict exists AND `pushed_at` newer than it)
  - `T2`: team-alias request AND touched `>= min_affinity_files` files
  - `T3`: remaining actionable PRs
- [x] 3.5 Remove the size small-PR points and wait-time points from the tier function (size/age become sort keys only)
- [x] 3.6 Update `tests/test_scoring.py` from `total_score` expectations to tier assertions, covering all four tiers plus a single-file T2 case

## 4. Gates: Re-review Carve-out

- [x] 4.1 Modify the already-reviewed rule in `gitkeeper/scoring/gates.py` to permit if `pr.pushed_at` is both present and greater than the user's latest review `submitted_at`
- [x] 4.2 Add a `drop_reason`/flag path for "re-review" status so consumers can render the badge
- [x] 4.3 Add `tests` covering: dropped when stale, retained as re-review when author pushed after review

## 5. Pipeline: Tier-Based Ordering

- [x] 5.1 Update `RelevancePipeline.process` to call the tier assigner and carry `pushed_at` through
- [x] 5.2 Replace the scalar sort in `gitkeeper/scoring/pipeline.py` with: actionable first, then `(tier, -heat, size, repo, number)` where heat = age of `pushed_at` and size = `additions + deletions`
- [x] 5.3 Keep non-actionable PRs at the tail as today (no numeric cutoff; every actionable PR visible)

## 6. UI: Labels and Rationale Chips

- [x] 6.1 Update `PRListView._populate_list` in `gitkeeper/ui/list_view.py` to render a tier label (e.g. `[T0]`) with the reason chip (e.g. `re-review`) instead of a numeric score / color band
- [x] 6.2 Update `PRListView.set_pull_requests` to sort by the new pipeline sort key (or consume the pipeline's already-sorted results consistently)
- [x] 6.3 Update `PROverviewView.update_pr` in `gitkeeper/ui/overview_view.py` to show the `tier` + rationale chips (drop the `Affinity: +x | Assignment: +y | Urgency: +z` breakdown and score color)
- [x] 6.4 Update `GitkeeperApp` in `gitkeeper/ui/app.py` to stop passing `min_threshold` and pass the replacement knob(s) / pipeline ordering
- [x] 6.5 Update `tests/test_ui.py` to assert tier label ordering instead of `total_score` ordering

## 7. Verification

- [x] 7.1 Run the full test suite (`pytest` with "root config"?) and check all scoring/gate/config/client/ui tests pass
- [x] 7.2 Manually exercise gitkeeper launch against a real token with a small queue — launch path (config → auth → fetch → tiering) verified against the live token; this surfaced that `pushedDate` is null for PR heads, so the payload now reads `committedDate` instead.
- [x] 7.3 Run `ruff` (or the project's configured linter) over changed files if configured