## Purpose

Provides an authenticated GitHub client to retrieve actionable pull requests, requested reviews, modified file paths, and CI/review status.

## ADDED Requirements

### Requirement: Authenticate with GitHub
The system SHALL support pluggable authentication providers to authenticate with the GitHub GraphQL and REST APIs.

#### Scenario: Authenticate using Personal Access Token
- **WHEN** a Personal Access Token is configured via config or environment
- **THEN** the system SHALL authenticate all GitHub API requests with bearer authorization

#### Scenario: Authentication failure handling
- **WHEN** the configured token is invalid, expired, or lacks necessary permissions
- **THEN** the system SHALL return a clear error message indicating the authentication failure

### Requirement: Fetch Pending Review Requests
The system SHALL query GitHub GraphQL API to fetch open pull requests where the user or the user's teams are requested reviewers.

#### Scenario: Fetch pull requests with review requests
- **WHEN** fetching review requests for a user
- **THEN** the system SHALL return open pull requests including repo name, PR number, title, author, draft status, review decisions, and list of modified file paths

#### Scenario: Batch query efficiency
- **WHEN** fetching details for multiple pull requests
- **THEN** the system SHALL retrieve PR metadata, modified paths, and status checks in a single batched GraphQL query
