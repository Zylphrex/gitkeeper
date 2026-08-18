## Why

The current composite score (0-100) collapses two orthogonal things — *who is waiting on me* and *how well suited I am to review* — into a single scalar. The result is that direct review requests get buried, genuinely hot "the author pushed after my feedback" PRs are filtered out entirely, and ties sort arbitrarily by GraphQL search order. Reviewers don't decide by comparing decimals; they decide by pressure bands ("do now," "this week," "whenever").

## What Changes

- **BREAKING** Replace the 0-100 scalar relevance score with a four-tier triage label (P0/T1/T2/T3) assigned by rule-based heuristics.
  - `P0 — You are the merge`: user is directly requested AND every other requested reviewer has already submitted a verdict (or the user is the only requested reviewer). CI must not be failing.
  - `T1 — Waiting on you`: user is directly requested, OR author activity landed recently (hot), OR a re-review is due.
  - `T2 — Team's, but yours`: team-alias request with meaningful local git affinity for the touched files.
  - `T3 — Everything else`: remaining actionable PRs (never hidden).
- Sort order: tier (P0 first) → last-activity heat (hottest first) → diff size (smallest first) → deterministic tie-breaks (repo, number). A directly-requested PR never ranks below a team-requested PR.
- **BREAKING** Remove the `min_score_threshold`-based hiding of sub-threshold PRs. Every actionable PR is labeled with its tier and sorted visibly.
- Add a **re-review carve-out** to the actionability gate: a PR the user already reviewed is NOT excluded if activity (author push) landed after the user's last verdict. It re-enters as a re-review item.
- **BREAKING** Fetch precise heat: add a timestamp for the latest commit push to the GraphQL query. "Hot" is derived from author push time, not PR `updatedAt` (which changes on comments and the user's own reviews).
- Replace the scalar breakdown UI (`[47]`, "Affinity: +X | Assignment: +Y | Urgency: +Z") with tier labels and reason chips (`P0 · re-review · touched by you`).
- Add tier-boundary configuration knobs, superseding `min_score_threshold`.

## Capabilities

### New Capabilities
- `triage-tiers`: Tier assignment rules, tier precedence, and heat-aware ordering for the actionable review queue.

### Modified Capabilities
- `relevance-scoring`: scoring behavior changes from a composite 0-100 scalar to triage tier labels with rationale chips; urgency/affinity heuristics feed tier assignment and intra-tier sorting rather than a summed score.
- `github-client`: the review-request query gains the latest commit's push/committed timestamp so heat and re-review detection use author activity.
- `tui-review-client`: the queue list and overview render tier labels and reason chips instead of numeric scores.

## Impact

- `gitkeeper/scoring/calculator.py` — replaced by a tier assigner
- `gitkeeper/scoring/gates.py` — re-review carve-out
- `gitkeeper/scoring/pipeline.py` — tier assignment, heat-based sorting, deterministic tie-breaks
- `gitkeeper/github/queries.py`, `gitkeeper/github/client.py` — latest-commit timestamp field
- `gitkeeper/config.py` — remove `min_score_threshold`, add tier-boundary and heat-window settings
- `gitkeeper/ui/list_view.py`, `gitkeeper/ui/overview_view.py` — tier label and reason-chip rendering
- `tests/` — scoring, gating, client parsing, and TUI snapshot tests