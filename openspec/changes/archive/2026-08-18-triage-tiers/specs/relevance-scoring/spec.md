## MODIFIED Requirements

### Requirement: Actionability Gating
The system SHALL filter out pull requests that are not currently ready or actionable for the user to review, while keeping recently-active previously-reviewed pull requests in the actionable queue as re-review items.

#### Scenario: Filter draft pull requests
- **WHEN** a pull request has draft status set to `true` and `ignore_drafts` is enabled
- **THEN** the system SHALL exclude the pull request from the actionable review queue

#### Scenario: Filter already reviewed pull requests with no new activity
- **WHEN** the user has already submitted an approved or changes-requested review for the latest commit AND no author activity has landed since that review
- **THEN** the system SHALL exclude the pull request from the actionable review queue

#### Scenario: Keep pull requests with new activity after the user's review
- **WHEN** the user has already submitted a review verdict for the pull request AND the author has pushed new commit activity after that verdict
- **THEN** the system SHALL keep the pull request in the actionable review queue and flag it as a re-review

### Requirement: Calculate Affinity and Urgency Score
The system SHALL compute heuristic signal inputs — local git affinity for touched files, assignment type, wait time, and review size — and SHALL NOT aggregate them into a composite 0-100 orderable score. The signals feed triage tier assignment and intra-tier queue ordering, and the composite score SHALL be removed from ranking output.

#### Scenario: Compute affinity signal for direct review on familiar code
- **WHEN** a user is directly requested on a PR where they authored recent commits on files touched by the PR
- **THEN** the system SHALL produce a recency-weighted affinity signal reflecting how recently and how broadly the user touched the changed files

#### Scenario: Compute alignment signal for team broadcast on unfamiliar code
- **WHEN** a PR is assigned via a team alias and the user has no commit history on the touched files
- **THEN** the system SHALL mark the affinity signal as low and the assignment as team-level, which ranks it below direct requests

#### Scenario: Wait-time urgency signal
- **WHEN** a pull request has kept an actionable state waiting for longer than a configured window
- **THEN** the system SHALL treat it as more age-urgent for intra-tier ordering without ever exceeding the pressure of an active author interaction