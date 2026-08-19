## MODIFIED Requirements

### Requirement: Actionability Gating
The system SHALL partition reviewed pull requests into action bands — _active_ (the ball is on the user), _waiting on author_ (the user requested changes and the author has not pushed since), or _waiting on others_ — and SHALL exclude pull requests that are not ready or actionable for anyone (drafts, closed pull requests, and failing-CI pull requests when configured), while keeping recently-active previously-reviewed pull requests in the active band as re-review items.

#### Scenario: Filter draft pull requests
- **WHEN** a pull request has draft status set to `true` and `ignore_drafts` is enabled
- **THEN** the system SHALL exclude the pull request from every band

#### Scenario: Filter closed pull requests
- **WHEN** a pull request is no longer open
- **THEN** the system SHALL exclude the pull request from every band

#### Scenario: Filter failing CI pull requests
- **WHEN** a pull request reports failing or erroring CI status and `ignore_failing_ci` is enabled
- **THEN** the system SHALL exclude the pull request from the active band and the waiting band

#### Scenario: Keep pull requests with new author activity after the user's review
- **WHEN** the user has already submitted a review verdict for the pull request AND the author has pushed new commit activity after that verdict
- **THEN** the system SHALL keep the pull request in the active band and flag it as a re-review

#### Scenario: Hold requested-changes pull requests as waiting on author
- **WHEN** the user's latest review verdict is CHANGES_REQUESTED AND no author push has landed since that verdict
- **THEN** the system SHALL NOT drop the pull request, and SHALL place it in the waiting-on-author band

#### Scenario: Hold approved pull requests as waiting on others
- **WHEN** the user's latest review verdict is APPROVED or DISMISSED and no author push has landed since
- **THEN** the system SHALL place the pull request in the waiting-on-others band

## ADDED Requirements

### Requirement: Assign Follow-up Turn State
The system SHALL classify each pull request into exactly one follow-up turn state — `ME_ACTIVE` (ball on the user), `WAITING_AUTHOR` (ball on the pull request author), or `WAITING_OTHERS` (ball on other reviewers, CI, or merge) — derived from the user's relationship to the pull request, the user's review verdicts, external reviewer verdicts, and the latest author push time, and SHALL NOT discard turn states by a numeric score threshold.

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
- **WHEN** the user is the author AND an external reviewer has submitted a verdict AFTER the user's latest push
- **THEN** the turn state SHALL be `ME_ACTIVE` and the pull request SHALL be flagged as a response to review feedback

#### Scenario: User's authored pull request is waiting on reviewers
- **WHEN** the user is the author AND no external reviewer has submitted a verdict after the user's latest push
- **THEN** the turn state SHALL be `WAITING_OTHERS`

#### Scenario: User approved and nothing needs the author
- **WHEN** the user's latest verdict is APPROVED and no author push has landed since
- **THEN** the turn state SHALL be `WAITING_OTHERS`

### Requirement: Flag Stale Follow-ups
The system SHALL track how long each `ME_ACTIVE` pull request has been waiting on the user and SHALL annotate those exceeding a configured staleness threshold, without ever filtering them out of the queue.

#### Scenario: A stale review request is flagged
- **WHEN** the user has been an outstanding requested reviewer for longer than `staleness_warn_after_days`
- **THEN** the system SHALL mark the pull request with a staleness indicator carrying the number of days outstanding

#### Scenario: A fresh pull request follow-up is not flagged
- **WHEN** the time the user has been the outstanding actor is within `staleness_warn_after_days`
- **THEN** the system SHALL NOT attach a staleness indicator

#### Scenario: Staleness counts from the user's outstanding act
- **WHEN** the user's outstanding action is a requested-changes re-review
- **THEN** the staleness age SHALL be measured from the author's latest push, not from the pull request creation