## REMOVED Requirements

### Requirement: Assign Triage Tier
**Reason**: Triage tiers (T0–T3) are removed from the product; queue rows no longer carry a tier label and the tier assignment heuristics (bottleneck, direct request, team affinity, diffusion) are deleted.
**Migration**: Delete every tier badge and tier title from the list and overview; stop assigning tiers in the scoring pipeline.

### Requirement: Order Triage Queue
**Reason**: The tier ordering requirement is replaced by recency ordering: the queue is a single flat sequence ordered by most recent activity, with no notion of tier, heat window, or review size as ordering keys.
**Migration**: Sort the queue by last-updated timestamp (newest first) with deterministic tie-breaking only.

### Requirement: Triage Authored Review-Response Items
**Reason**: The "ball on the user" case for authored pull requests with fresh external verdicts is still recognized as a turn state, but it is no longer promoted into a numeric tier (T1); the overview rationale conveys the reason instead.
**Migration**: Classify authored pull requests with fresh reviewer feedback as awaiting-action; show "respond to review" as a rationale chip.

### Requirement: Order the Waiting Band
**Reason**: The waiting band and its "oldest wait first" ordering are removed; waiting pull requests are interleaved with awaiting-action pull requests in the single recency-ordered queue, each row labeled with its turn state.
**Migration**: Remove band ordering and band separator rendering; waiting pull requests appear at their natural recency position with a waiting-label badge.