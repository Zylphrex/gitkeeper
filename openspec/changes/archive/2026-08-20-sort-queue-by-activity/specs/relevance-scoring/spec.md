## MODIFIED Requirements

### Requirement: Actionability Gating
The system SHALL gate reviewed pull requests by actionability alone — excluding pull requests that are not ready or actionable for anyone (drafts, closed pull requests, and failing-CI pull requests when configured) — and SHALL classify every surviving pull request into exactly one follow-up turn state, keeping recently-active previously-reviewed pull requests classified as re-review items rather than dropping them.

#### Scenario: Filter draft pull requests
- **WHEN** a pull request has draft state set to `true` and `ignore_drafts` is enabled
- **THEN** the system SHALL exclude the pull request from the queue

#### Scenario: Filter closed pull requests
- **WHEN** a pull request is no longer open
- **THEN** the system SHALL exclude the pull request from the queue

#### Scenario: Filter failing CI pull requests
- **WHEN** a pull request reports failing or erroring CI status and `ignore_failing_ci` is enabled
- **THEN** the system SHALL exclude the pull request from the queue

#### Scenario: Keep pull requests with new author activity after the user's review
- **WHEN** the user has already submitted a review verdict for the pull request AND the author has pushed new commit activity after that verdict
- **THEN** the system SHALL keep the pull request in the queue and flag it as a re-review

#### Scenario: Hold requested-changes pull requests as waiting on author
- **WHEN** the user's latest review verdict is CHANGES_REQUESTED AND no author push has landed since that verdict
- **THEN** the system SHALL NOT drop the pull request, and SHALL classify it as waiting on author

#### Scenario: Hold approved pull requests as waiting on others
- **WHEN** the user's latest review verdict is APPROVED or DISMISSED and no author push has landed since
- **THEN** the system SHALL classify the pull request as waiting on others

## ADDED Requirements

### Requirement: Order Queue by Recent Activity
The system SHALL order all actionable pull requests in a single flat sequence by most recent activity (newest first) using the pull request's last-updated timestamp, with deterministic tie-breaking, and SHALL NOT reorder them by tier, affiliation score, heat window, or wait age.

#### Scenario: Newest activity first
- **WHEN** the queue holds multiple actionable pull requests with different last-updated timestamps
- **THEN** the system SHALL place the pull request updated most recently first in the queue
- **AND** the system SHALL derive recency from GitHub's last-updated timestamp, which reflects commits, comments, reviews, and state changes

#### Scenario: Deterministic tie-break
- **WHEN** two pull requests share the same last-updated time
- **THEN** the system SHALL order them deterministically by repository name and then pull request number

#### Scenario: Waiting and active stay interleaved
- **WHEN** the queue holds a mix of awaiting-action and waiting pull requests
- **THEN** the system SHALL order them together by recent activity rather than separating them into bands
- **AND** a waiting pull request with newer activity SHALL appear ahead of an awaiting-action pull request with older activity

### Requirement: Compute Affinity Context for Overview
The system SHALL compute local git touch context for the files a pull request changes — without using it to rank or order the queue — so the overview can show why the pull request may be relevant to the user.

#### Scenario: Touched files within lookback window
- **WHEN** the user has authored recent commits on paths touched by the pull request and a local clone is available
- **THEN** the system SHALL compute the touched-file count and SHALL surface it as contextual rationale in the overview

#### Scenario: No local clone
- **WHEN** a pull request's repository has no corresponding local clone on disk
- **THEN** the system SHALL not fail the score and SHALL omit the touched-files context from the overview

## REMOVED Requirements

### Requirement: Flag Stale Follow-ups
**Reason**: The staleness marker is removed from the UI and the recency ordering replaces any need to decorate stale rows; stale-follow-up reasoning no longer influences display.
**Migration**: Remove the staleness marker from the UI and row output; no config replaces it.

### Requirement: Calculate Affinity and Urgency Score
**Reason**: The composite signal model that fed tier assignment and intra-tier queue ordering is removed with the triage tiers; queue order is now recency-only and affinity survives only as overview context.
**Migration**: Queue ordering is determined by most-recent activity; the touched-files signal is surfaced only in the overview panel.