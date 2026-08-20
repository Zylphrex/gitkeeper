## MODIFIED Requirements

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
