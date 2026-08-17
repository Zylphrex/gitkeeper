## MODIFIED Requirements

### Requirement: Display Prioritized Review Queue
The system SHALL provide a CLI command to fetch, score, rank, and display actionable review requests in a formatted terminal table.

#### Scenario: Display queue of prioritized PRs
- **WHEN** user executes `gitkeeper queue` (or `gitkeeper list`)
- **THEN** the system SHALL display a ranked table of PRs with columns for Score, PR number, Repository, Author, Title, and Rationale
- **AND** the PR number column SHALL be formatted as a clickable terminal hyperlink to the PR URL when a URL is available

#### Scenario: Hide low-relevance ambient PRs below threshold
- **WHEN** PRs score below `min_score_threshold`
- **THEN** the system SHALL exclude them from the default view and display a count of hidden ambient PRs with a suggestion to use `--all`

#### Scenario: View all PRs including low-relevance ones
- **WHEN** user executes `gitkeeper queue --all`
- **THEN** the system SHALL render all actionable PRs regardless of score threshold
