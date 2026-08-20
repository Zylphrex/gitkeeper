## Purpose

Evaluates pull requests against actionability filters, follow-up turn states, and local-git affinity context to decide which requests belong in the review queue.

## Requirements

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

### Requirement: Assign Follow-up Turn State
The system SHALL classify each pull request into exactly one follow-up turn state — `ME_ACTIVE` (ball on the user), `WAITING_AUTHOR` (ball on the pull request author), or `WAITING_OTHERS` (ball on other reviewers, CI, or merge) — derived from the user's relationship to the pull request, including pull requests the user has reviewed, the user's review verdicts, external reviewer verdicts, and the latest author push time, and SHALL NOT discard turn states by a numeric score threshold. An external approval SHALL NOT place the ball on the user; a response is required only when the external verdict demands one (such as `CHANGES_REQUESTED`).

#### Scenario: Review is due on the user
- **WHEN** the user is a requested reviewer AND has no submitted verdict and no author activity after the pull request became actionable
- **THEN** the turn state SHALL be `ME_ACTIVE`

#### Scenario: Re-review is due on the user
- **WHEN** the user has submitted a verdict AND the author has pushed new commits after it
- **THEN** the turn state SHALL be `ME_ACTIVE` and the pull request SHALL be flagged as a re-review

#### Scenario: User is waiting on the author to respond
- **WHEN** the user's latest verdict is CHANGES_REQUESTED and the author has not pushed after it
- **THEN** the turn state SHALL be `WAITING_AUTHOR`

#### Scenario: User's authored pull request has fresh reviewer feedback
- **WHEN** the user is the author AND an external reviewer has submitted a CHANGES_REQUESTED verdict (or other verdict that requires a response) AFTER the user's latest push
- **THEN** the turn state SHALL be `ME_ACTIVE` and the pull request SHALL be flagged as a response to review feedback

#### Scenario: User's authored pull request is externally approved
- **WHEN** the user is the author AND the latest external verdict is APPROVED, with no further response-requiring verdict after the user's latest push
- **THEN** the turn state SHALL be `WAITING_OTHERS` and the pull request SHALL be labeled as approved and waiting to merge, not as a response to review feedback

#### Scenario: User's authored pull request is waiting on reviewers
- **WHEN** the user is the author AND no external reviewer verdict requiring a response has been submitted after the user's latest push
- **THEN** the turn state SHALL be `WAITING_OTHERS`

#### Scenario: User approved and nothing needs the author
- **WHEN** the user's latest verdict is APPROVED and no author push has landed since
- **THEN** the turn state SHALL be `WAITING_OTHERS`

#### Scenario: User reviewed pull request the author then updated
- **WHEN** the user is not the author AND has submitted a review verdict AND the author has pushed new commits after it
- **THEN** the turn state SHALL be `ME_ACTIVE` and the pull request SHALL be flagged as a re-review

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