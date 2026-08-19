## ADDED Requirements

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