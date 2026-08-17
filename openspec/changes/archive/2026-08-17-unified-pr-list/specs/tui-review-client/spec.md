## MODIFIED Requirements

### Requirement: Interactive PR Queue Navigation
The system SHALL provide a full-screen interactive interface listing actionable pull requests ranked by relevance score in a singular continuous list with keyboard and mouse navigation.

#### Scenario: Navigate ranked pull requests
- **WHEN** the TUI application loads
- **THEN** the system SHALL display the complete ranked list of actionable pull requests in the left panel sorted descending by relevance score with relevance scores, repository names, and authors
- **AND** the user SHALL be able to select and highlight different pull requests using keyboard navigation (e.g. arrow keys or j/k) or mouse selection

#### Scenario: Display selected PR overview and rationale
- **WHEN** a pull request is selected or clicked in the queue list
- **THEN** the system SHALL display the PR metadata, full description, and detailed scoring rationale breakdown in the right overview panel
- **AND** the system SHALL synchronize the diff viewer with the newly selected pull request
