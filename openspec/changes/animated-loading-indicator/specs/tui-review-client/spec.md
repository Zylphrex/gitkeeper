## MODIFIED Requirements

### Requirement: Top Header Status and Refresh Tracking
The system SHALL display an application header indicating active background tasks and the timestamp of the last successful queue refresh.

#### Scenario: Display idle state with last refreshed timestamp
- **WHEN** no background network or scoring operations are active
- **THEN** the header SHALL show the last refreshed time (or initial status if no refresh has completed)

#### Scenario: Display active background operation
- **WHEN** a queue refresh or initial fetch is executing in the background
- **THEN** the header SHALL display an active status message describing the current stage (e.g. fetching GitHub data or scoring relevance)
- **AND** the message SHALL lead with an animated spinner that cycles through frames while the operation is active

### Requirement: Diff View Asynchronous Loading State
The system SHALL provide explicit visual loading indicators in the diff viewer when fetching patches asynchronously.

#### Scenario: Display loading state while fetching diff
- **WHEN** a pull request is selected whose diff is not currently cached
- **THEN** the diff view SHALL display a loading indicator until the patch data is retrieved and rendered
- **AND** the loading indicator SHALL animate while the patch is being fetched

#### Scenario: Display error state on diff fetch failure
- **WHEN** fetching a pull request patch fails
- **THEN** the diff view SHALL display a clear error message explaining the failure
- **AND** the loading indicator SHALL stop animating