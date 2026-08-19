## ADDED Requirements

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