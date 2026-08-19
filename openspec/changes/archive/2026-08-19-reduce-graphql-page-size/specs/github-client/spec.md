## MODIFIED Requirements

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