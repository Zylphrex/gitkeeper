## Purpose

Provides a CLI command suite and terminal formatting to present prioritized pull request queues with contextual rationale.

## Requirements

### Requirement: Display Prioritized Review Queue
The system SHALL launch an interactive full-screen terminal user interface directly when invoked as `gitkeeper` without requiring any subcommands, displaying all actionable pull requests in a singular unified queue ordered by relevance.

#### Scenario: Launch interactive TUI review queue
- **WHEN** user executes `gitkeeper`
- **THEN** the system SHALL directly launch the interactive full-screen TUI with the complete prioritized list of actionable review requests sorted by relevance score
