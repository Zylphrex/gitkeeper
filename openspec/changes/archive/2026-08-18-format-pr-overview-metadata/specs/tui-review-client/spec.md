## MODIFIED Requirements

### Requirement: Interactive PR Queue Navigation
The system SHALL provide a full-screen interactive interface listing actionable pull requests ranked by relevance score in a singular continuous list with keyboard and mouse navigation.

#### Scenario: Navigate ranked pull requests
- **WHEN** the TUI application loads
- **THEN** the system SHALL display the complete ranked list of actionable pull requests in the left panel sorted descending by relevance score with relevance scores, repository names, and authors
- **AND** the user SHALL be able to select and highlight different pull requests using keyboard navigation (e.g. arrow keys or j/k) or mouse selection

#### Scenario: Display selected PR overview and rationale
- **WHEN** a pull request is selected or clicked in the queue list
- **THEN** the system SHALL display the PR metadata, full description, and detailed scoring rationale breakdown in a persistent overview section on the far right
- **AND** the metadata SHALL be rendered in full: any metadata line that exceeds the overview panel width SHOULD wrap at the panel edge and never be clipped or overflow off-screen
- **AND** the metadata SHALL include the repository, author, draft state, base and head branch refs, CI status, addition/deletion counts, changed file count, created date, relative time since last update, requested reviewers, and a compact summary of existing reviews
- **AND** the metadata and scoring rationale boxes SHALL size to their content so the PR body retains the remaining panel height
- **AND** the overview section SHALL remain visible while the user inspects the Files & Diff pane for the selected pull request
- **AND** the system SHALL synchronize the diff viewer with the newly selected pull request

#### Scenario: Overview is not a tab
- **WHEN** the TUI application loads with the Files & Diff pane active
- **THEN** the overview section SHALL be visible on the far right without requiring tab switching
- **AND** the overview section SHALL NOT be selectable as a tab