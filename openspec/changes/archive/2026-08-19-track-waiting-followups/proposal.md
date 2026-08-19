## Why

gitkeeper only knows one relationship: "a review has been requested from me." That leaves three blind spots that make PRs slip through: my requested reviews that sit unacted for days (staleness), my own authored PRs that got fresh reviewer feedback I need to answer, and the balls I have already thrown — PRs where I requested changes and am now waiting on the author. Identifying "what needs my attention" means tracking whose turn it is, not just who asked me.

## What Changes

- Widen the fetch to include open PRs I **authored** (`author:@me`), in addition to PRs where I'm a requested reviewer. The commenter/thread-reply surface is explicitly out of scope; reply detection stays cheap and push-based.
- Derive a **turn state** per PR from timestamps already fetched (my last verdict, latest author push): ball on me (`ME_ACTIVE`), ball on author (`WAITING_AUTHOR`), or ball elsewhere (`WAITING_OTHERS`).
- Keep the triage-tier machinery (T0–T3) only for ball-on-me items; ball-on-others items move to an **always-visible dimmed band** at the bottom of the queue instead of vanishing after I review.
- Mark **staleness** on ball-on-me items ("waiting on you for N days") as a flag, never a filter.
- Add a `followup` configuration block enabling authored-PR collection, the waiting band, and the staleness threshold.

## Capabilities

### New Capabilities
<!-- none: the follow-up turn model extends existing scoring, queue, and UI capabilities. -->

### Modified Capabilities
- `github-client`: Add a fetch path for open pull requests authored by the current user, reusing the existing page payload, pagination, and retry behavior.
- `relevance-scoring`: Classify each pull request by follow-up turn state (ball on me, waiting on author, waiting on others) and annotate stale ball-on-me items, replacing the current "unreviewed → dropped" behavior with a persistent waiting band.
- `triage-tiers`: Rank authored-PR review responses alongside directly-requested work, and order the waiting band (oldest of my actions first) without delisting waiting items by score.
- `config-management`: Add the `followup` block — `include_authored`, `show_waiting_on_author`, `show_waiting_on_others`, and `staleness_warn_after_days`.
- `tui-review-client`: Render the always-visible waiting band below the triaged queue with dimmed styling, and display the staleness indicator on ball-on-me queue entries.

## Impact

- `gitkeeper/github/client.py` + `queries.py`: new authored-PR search source reusing `REVIEW_REQUESTS_QUERY` payload.
- `gitkeeper/scoring/pipeline.py` + `calculator.py`: turn-state derivation and waiting-band classification feeding `ScoredPullRequest`.
- `gitkeeper/config.py`: `FollowupConfig`; `load_config` wiring.
- `gitkeeper/ui/app.py`: queue split into triaged section + waiting band; staleness marker pass-through.
- `gitkeeper/ui/list_view.py` / `overview_view.py`: band rendering and stale-flag line.
- Tests under `tests/` for turn-state derivation, waiting-band sorting, and config parsing.