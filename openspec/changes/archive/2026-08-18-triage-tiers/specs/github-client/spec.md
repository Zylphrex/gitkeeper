## MODIFIED Requirements

### Requirement: Fetch Pending Review Requests
The system SHALL query GitHub GraphQL API to fetch open pull requests where the user or the user's teams are requested reviewers, including the timestamp of the most recent author commit so that heat and re-review detection reflect author activity rather than incidental PR updates.

#### Scenario: Fetch pull requests with review requests
- **WHEN** fetching review requests for a user
- **THEN** the system SHALL return open pull requests including repo name, PR number, title, author, draft status, review decisions, list of modified file paths, the base and head branch ref names, and the latest-commit push timestamp for heat and re-review detection

#### Scenario: Batch query efficiency
- **WHEN** fetching details for multiple pull requests
- **THEN** the system SHALL retrieve PR metadata, branch refs, modified paths, status check results, and the latest commit timestamp in a single batched GraphQL query