## MODIFIED Requirements

### Requirement: Display Prioritized Review Queue
The system SHALL launch an interactive full-screen terminal user interface directly when invoked as `gitkeeper` without requiring any subcommands.

#### Scenario: Launch interactive TUI review queue
- **WHEN** user executes `gitkeeper`
- **THEN** the system SHALL directly launch the interactive full-screen TUI with the prioritized list of review requests

#### Scenario: Hide low-relevance ambient PRs below threshold
- **WHEN** PRs score below `min_score_threshold`
- **THEN** the system SHALL exclude them from the primary queue view and indicate ambient PRs with a toggle or filter to view them within the TUI

#### Scenario: View all PRs including low-relevance ones
- **WHEN** user toggles ambient PRs within the TUI
- **THEN** the system SHALL display all actionable PRs regardless of score threshold
