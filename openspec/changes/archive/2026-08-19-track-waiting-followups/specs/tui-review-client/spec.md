## ADDED Requirements

### Requirement: Render the Waiting Band
The system SHALL render the waiting band (waiting-on-author and waiting-on-others pull requests) as an always-visible, dimmed section below the active triaged queue, visually separated, selectable for inspection without requiring a tab switch.

#### Scenario: Display the waiting band below the active queue
- **WHEN** the queue contains both active and waiting-band pull requests
- **THEN** the list SHALL render every active pull request first followed by a visually separated, dimmed waiting band containing the waiting pull requests
- **AND** the waiting band SHALL remain always visible without any tab switching or scroll-dependent reveal

#### Scenario: Identify the reason a pull request is waiting
- **WHEN** a waiting-band entry is rendered
- **THEN** the entry SHALL convey why it is waiting (waiting on author, awaiting reviewers, or approved) alongside the repository name and pull request number

#### Scenario: Inspect a waiting pull request
- **WHEN** the user navigates the cursor into the waiting band and selects an entry
- **THEN** the overview panel SHALL display that pull request's metadata and rationale, including its turn state

#### Scenario: Waiting band hidden by configuration
- **WHEN** both waiting-band display settings are disabled
- **THEN** the system SHALL NOT render a waiting band or its section separator

### Requirement: Display Staleness on Active Follow-ups
The system SHALL surface the staleness indicator on active-band pull request entries once the follow-up has been waiting on the user longer than the configured staleness threshold.

#### Scenario: Stale active entry shows its outstanding age
- **WHEN** an active-band entry has been waiting on the user longer than `followup.staleness_warn_after_days`
- **THEN** the entry's metadata row SHALL display a staleness marker carrying the number of days the follow-up has been outstanding alongside the triage tier label

#### Scenario: Fresh active entry shows no staleness marker
- **WHEN** an active-band entry has been waiting on the user within the staleness threshold
- **THEN** the entry's metadata row SHALL NOT display a staleness marker