## MODIFIED Requirements

### Requirement: Fetch Pending Review Requests
The system SHALL query GitHub GraphQL API to fetch open pull requests where the user or the user's teams are requested reviewers.

#### Scenario: Fetch pull requests with review requests
- **WHEN** fetching review requests for a user
- **THEN** the system SHALL return open pull requests including repo name, PR number, title, author, draft status, review decisions, list of modified file paths, and the base and head branch ref names

#### Scenario: Batch query efficiency
- **WHEN** fetching details for multiple pull requests
- **THEN** the system SHALL retrieve PR metadata, branch refs, modified paths, and status check results in a single batched GraphQL query