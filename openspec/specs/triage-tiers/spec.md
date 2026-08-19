## Purpose

Assigns each actionable pull request a bounded triage tier and a deterministic ordering, so reviewers see pressure bands ("do now," "on you," "this week," "whenever") instead of trusting a flat composite number.

## Requirements

### Requirement: Assign Triage Tier
The system SHALL assign exactly one of four tiers (_T0_, _T1_, _T2_, _T3_) to each actionable pull request based on assignment type, reviewer verdict pressure, local git affinity, and author activity, and SHALL NOT determine queue ordering by a composite numeric score.

#### Scenario: You are the bottleneck
- **WHEN** the user is a directly requested reviewer AND every other requested reviewer has already submitted a review verdict (approved, dismissed, or requested changes) OR the user is the only requested reviewer
- **THEN** the pull request SHALL be assigned the top tier, _T0_

#### Scenario: Directly requested
- **WHEN** the user is a directly requested reviewer but other requested reviewers have not yet all submitted verdicts
- **THEN** the pull request SHALL be assigned to _T1_

#### Scenario: Author is actively pushing
- **WHEN** the pull request's latest commit or push activity is within the configured hotness window
- **THEN** the pull request SHALL be assigned to _T1_ as a hot item

#### Scenario: Re-review is due
- **WHEN** the user has previously submitted a review verdict AND the author has pushed new commit activity after that verdict
- **THEN** the pull request SHALL be assigned to _T1_ and flagged as a re-review

#### Scenario: Team-requested with local affinity
- **WHEN** the pull request is requested via a team alias the user belongs to AND the user has touched a meaningful portion of the changed files within the git lookback window
- **THEN** the pull request SHALL be assigned to _T2_

#### Scenario: Everything else actionable
- **WHEN** the pull request is actionable but does not match any higher-tier rule
- **THEN** it SHALL be assigned to the lowest visible tier, _T3_

### Requirement: Order Triage Queue
The system SHALL sort actionable pull requests by tier, then heat, then review effort, with deterministic tie-breaking, and SHALL NOT discard any actionable pull request based on a numeric score threshold.

#### Scenario: Order by heat within tier
- **WHEN** multiple actionable pull requests share the same tier
- **THEN** the system SHALL sort them by most recent author push/activity first, then by smallest diff size, then deterministically by repository name and pull request number

#### Scenario: Never rank below a team ask
- **WHEN** a pull request directly requests the user's review AND another pull request is only team-assigned
- **THEN** the directly requested pull request SHALL be ordered before the team-assigned one regardless of local affinity or diff size
### Requirement: Triage Authored Review-Response Items
The system SHALL assign a pull request authored by the user, on which an external reviewer has submitted a verdict after the user's latest push, to the second-highest tier (_T1_) so a response to review feedback is not ranked below team asks.

#### Scenario: Reviewer feedback lands on the user's pull request
- **WHEN** the user is the author of the pull request AND an external reviewer's verdict was submitted after the user's latest push
- **THEN** the pull request SHALL be assigned _T1_ and the rationale SHALL include the reason "respond to review"

#### Scenario: No fresh feedback on the user's pull request
- **WHEN** the user is the author of the pull request AND no external reviewer verdict has been submitted after the user's latest push
- **THEN** the pull request SHALL be placed in the waiting band instead of the active tiered queue

### Requirement: Order the Waiting Band
The system SHALL sort waiting-band pull requests (waiting on author and waiting on others) after every active-band pull request, ordering the waiting items by the time the user's own action was most recently waited on, oldest first, with deterministic tie-breaking, and SHALL NOT order waiting-band items by their numeric relevance or discard any waiting-band item by a score threshold.

#### Scenario: Waiting on author items surface oldest first
- **WHEN** multiple pull requests are waiting on their authors in the waiting band
- **THEN** the system SHALL order them by the age of the user's last verdict, the one the user has been waiting on longest first, then deterministically by repository name and pull request number

#### Scenario: Active items always precede waiting items
- **WHEN** the queue holds both active and waiting-band pull requests
- **THEN** every active-band pull request SHALL be ordered before every waiting-band pull request regardless of the active item's heat, size, or tier

#### Scenario: Waiting band can be hidden by configuration
- **WHEN** the user has disabled the corresponding waiting-band display setting
- **THEN** the system SHALL NOT render that band, and SHALL NOT affect the ordering of active-band pull requests
