## MODIFIED Requirements

### Requirement: Display Prioritized Review Queue
The system SHALL launch an interactive full-screen terminal user interface directly when invoked as `gitkeeper` without requiring any subcommands, displaying all actionable pull requests in a singular unified queue ordered by relevance.

#### Scenario: Launch interactive TUI review queue
- **WHEN** user executes `gitkeeper`
- **THEN** the system SHALL directly launch the interactive full-screen TUI with the complete prioritized list of actionable review requests sorted by relevance score

## REMOVED Requirements

### Requirement: Hide low-relevance ambient PRs below threshold
**Reason**: Replaced by a singular unified review list displaying all actionable PRs sorted descending by relevance score, removing the separation of low-relevance PRs into a separate view or tab.
**Migration**: All actionable PRs are visible directly in the main review list sorted by relevance score.

### Requirement: View all PRs including low-relevance ones
**Reason**: Replaced by a singular unified review list that always includes all actionable PRs by default.
**Migration**: No toggle or secondary view is required since all actionable PRs are already present in the unified list.
