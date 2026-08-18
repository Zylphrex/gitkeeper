## Purpose

Provides an authenticated GitHub client to retrieve actionable pull requests, requested reviews, modified file paths, and CI/review status.

## Requirements

### Requirement: Authenticate with GitHub
The system SHALL support pluggable authentication providers to authenticate with the GitHub GraphQL and REST APIs.

#### Scenario: Authenticate using Personal Access Token
- **WHEN** a Personal Access Token is configured via config or environment
- **THEN** the system SHALL authenticate all GitHub API requests with bearer authorization

#### Scenario: Authentication failure handling
- **WHEN** the configured token is invalid, expired, or lacks necessary permissions
- **THEN** the system SHALL return a clear error message indicating the authentication failure

### Requirement: Fetch Pending Review Requests
The system SHALL query the GitHub GraphQL API to fetch the complete set of open pull requests where the user or the user's teams are requested reviewers, including the timestamp of the most recent author commit so that heat and re-review detection reflect author activity rather than incidental PR updates. The system SHALL paginate through all results of the query so that the returned set is not limited to a single page.

#### Scenario: Fetch pull requests with review requests
- **WHEN** fetching review requests for a user
- **THEN** the system SHALL return all open pull requests (across all pages) including repo name, PR number, title, author, draft status, review decisions, list of modified file paths, the base and head branch ref names, and the latest-commit push timestamp for heat and re-review detection

#### Scenario: Complete results across multiple pages
- **WHEN** the query returns more pull requests than fit in a single result page
- **THEN** the system SHALL continue fetching subsequent pages until all matching pull requests are retrieved, and SHALL return each pull request once

#### Scenario: Batch query efficiency
- **WHEN** fetching details for multiple pull requests
- **THEN** the system SHALL retrieve PR metadata, branch refs, modified paths, status check results, and the latest commit timestamp in a single batched GraphQL query per page

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
