## ADDED Requirements

### Requirement: Fetch Pull Request Diff
The system SHALL retrieve unified diff patches and file modifications for a pull request from the GitHub API.

#### Scenario: Retrieve PR diff contents
- **WHEN** fetching diff details for a specific pull request
- **THEN** the system SHALL return the unified diff patch or file change chunks from GitHub

### Requirement: Submit Pull Request Review Mutation
The system SHALL submit pull request review decisions (APPROVE, REQUEST_CHANGES, COMMENT) and associated line-level comments to GitHub.

#### Scenario: Submit pull request review with comments
- **WHEN** submitting a review with an event type, body message, and list of draft comments
- **THEN** the system SHALL execute the review mutation against the GitHub API and return the created review status
