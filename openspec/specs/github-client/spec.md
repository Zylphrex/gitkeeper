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
The system SHALL query the GitHub GraphQL API to fetch the complete set of open pull requests where the user or the user's teams are requested reviewers, including the timestamp of the most recent author commit so that heat and re-review detection reflect author activity rather than incidental PR updates. The system SHALL paginate through all results of the query so that the returned set is not limited to a single page. Each page SHALL request no more than 25 pull requests so that individual requests stay small enough for the GitHub gateway to serve reliably. When the GitHub API answers a page request with a transient server error (HTTP 5xx, such as 502), the system SHALL retry that page with exponential backoff, up to 2 additional attempts, before reporting a failure.

#### Scenario: Fetch pull requests with review requests
- **WHEN** fetching review requests for a user
- **THEN** the system SHALL return all open pull requests (across all pages) including repo name, PR number, title, author, draft status, review decisions, list of modified file paths, the base and head branch ref names, and the latest-commit push timestamp for heat and re-review detection

#### Scenario: Complete results across multiple pages
- **WHEN** the query returns more pull requests than fit in a single result page
- **THEN** the system SHALL continue fetching subsequent pages until all matching pull requests are retrieved, and SHALL return each pull request once

#### Scenario: Small page size
- **WHEN** the system issues a page request to the GraphQL search API
- **THEN** the request SHALL fetch no more than 25 pull requests at a time

#### Scenario: Transient server error is retried
- **WHEN** the GitHub API responds to a page request with an HTTP 5xx error (e.g., 502) on the first or second attempt
- **THEN** the system SHALL back off and retry the request, for up to two additional attempts, and continue pagination if a retry succeeds

#### Scenario: Server error persists after retries
- **WHEN** all retry attempts for a page return an HTTP 5xx error
- **THEN** the system SHALL raise the error as a refresh failure

#### Scenario: Batch query efficiency
- **WHEN** fetching details for multiple pull requests
- **THEN** the system SHALL retrieve PR metadata, branch refs, modified paths, status check results, and the latest commit timestamp in a single batched GraphQL query per page

### Requirement: Fetch Authored Pull Requests
The system SHALL fetch open pull requests authored by the current user, in addition to pull requests where the user is a requested reviewer, using the same per-page payload, page size, pagination, and transient-server-error retry behavior as the review-request search.

#### Scenario: Fetch authored pull requests
- **WHEN** the client fetches pull requests for the authenticated user
- **THEN** the system SHALL issue a search query `is:open is:pr author:@me archived:false` (or its per-user equivalent)
- **AND** the system SHALL include the returned pull requests in the queue data alongside review-requested pull requests

#### Scenario: Complete authored results across multiple pages
- **WHEN** the authored search returns more pull requests than fit in a single result page
- **THEN** the system SHALL continue fetching subsequent pages until all authored pull requests are retrieved and SHALL return each pull request once with the same pull request id

#### Scenario: Page size and retry behavior are shared
- **WHEN** the system issues any page request for the authored search
- **THEN** the request SHALL fetch no more than 25 pull requests at a time
- **AND** a transient HTTP 5xx response SHALL be retried with backoff, up to two additional attempts, before reporting a refresh failure

#### Scenario: Authored fetch failure
- **WHEN** all retry attempts for the authored query fail
- **THEN** the system SHALL raise the error as a refresh failure and keep previously fetched queue data visible

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
