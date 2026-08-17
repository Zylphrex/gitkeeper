## MODIFIED Requirements

### Requirement: Manual Queue Refresh
The system SHALL provide a manual refresh trigger to re-query GitHub and re-score the queue on demand while providing non-blocking visual progress feedback.

#### Scenario: Trigger manual refresh
- **WHEN** the user presses the refresh key
- **THEN** the system SHALL trigger asynchronous background fetching from GitHub and relevance re-scoring
- **AND** the system SHALL display the current background activity stage in the top header without blocking queue navigation
- **AND** the system SHALL update the last refreshed timestamp upon completion

#### Scenario: Handle refresh errors gracefully
- **WHEN** a background refresh operation fails
- **THEN** the system SHALL report the failure in the status display
- **AND** the system SHALL keep existing queue items visible and interactive

## ADDED Requirements

### Requirement: Top Header Status and Refresh Tracking
The system SHALL display an application header indicating active background tasks and the timestamp of the last successful queue refresh.

#### Scenario: Display idle state with last refreshed timestamp
- **WHEN** no background network or scoring operations are active
- **THEN** the header SHALL show the last refreshed time (or initial status if no refresh has completed)

#### Scenario: Display active background operation
- **WHEN** a queue refresh or initial fetch is executing in the background
- **THEN** the header SHALL display an active status message describing the current stage (e.g. fetching GitHub data or scoring relevance)

### Requirement: Diff View Asynchronous Loading State
The system SHALL provide explicit visual loading indicators in the diff viewer when fetching patches asynchronously.

#### Scenario: Display loading state while fetching diff
- **WHEN** a pull request is selected whose diff is not currently cached
- **THEN** the diff view SHALL display a loading indicator until the patch data is retrieved and rendered

#### Scenario: Display error state on diff fetch failure
- **WHEN** fetching a pull request patch fails
- **THEN** the diff view SHALL display a clear error message explaining the failure
