## MODIFIED Requirements

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