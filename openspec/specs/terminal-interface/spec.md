## Purpose

Provides a CLI command suite and terminal formatting to present prioritized pull request queues with contextual rationale.

## Requirements

### Requirement: Display Prioritized Review Queue
The system SHALL launch an interactive full-screen terminal user interface directly when invoked as `gitkeeper` without requiring any subcommands, displaying all actionable pull requests in a singular unified queue ordered by relevance.

The system SHALL render a preview of the selected pull request, including its markdown description, in the overview panel, and SHALL manage preview updates so that only the latest preview is rendered. When navigation or queue refreshes supersede a previous preview render, the superseded render SHALL be cancelled without leaking unhandled asyncio cancellation errors during shutdown.

The system SHALL NOT re-render the overview panel when a pull request with identical description body is re-selected or re-issued.

#### Scenario: Launch interactive TUI review queue
- **WHEN** user executes `gitkeeper`
- **THEN** the system SHALL directly launch the interactive full-screen TUI with the complete prioritized list of actionable review requests sorted by relevance score

#### Scenario: Rapidly navigate queue then quit
- **WHEN** user rapidly highlights multiple pull requests in the queue and then quits the application before all previews have finished rendering
- **THEN** the application SHALL shut down without emitting unhandled asyncio `CancelledError` warnings for superseded preview renders

#### Scenario: Re-select the currently displayed pull request
- **WHEN** the same pull request is re-selected or its description is re-issued without changes
- **THEN** the system SHALL NOT re-parse or re-render the pull request body preview

### Requirement: CLI help does not advertise completion options
The system SHALL NOT list `--install-completion` or `--show-completion` in the `gitkeeper` CLI help options panel when help is displayed (invoked with `--help` or as a group help output), and SHALL NOT register either option for parsing on the root command.

#### Scenario: Help invoked shows no completion options
- **WHEN** a user invokes `gitkeeper --help`
- **THEN** the options panel SHALL contain `--config` and `--help` but SHALL NOT contain `--install-completion` or `--show-completion`

#### Scenario: Completion flags are rejected
- **WHEN** a user invokes `gitkeeper --install-completion` or `gitkeeper --show-completion`
- **THEN** the system SHALL respond as with any unknown option, and SHALL NOT install or display shell completion scripts
