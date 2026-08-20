## ADDED Requirements

### Requirement: Fetch Reviewed Pull Requests
The system SHALL fetch open pull requests the user has reviewed, in addition to review-requested and authored pull requests, using the same per-page payload, page size, pagination, and transient-server-error retry behavior as the review-request search, so that reviewed pull requests remain visible until they are merged rather than disappearing when the user is de-listed as a requested reviewer.

#### Scenario: Fetch reviewed pull requests
- **WHEN** the client fetches pull requests for the authenticated user
- **THEN** the system SHALL issue a search query `is:open is:pr reviewed-by:@me archived:false` (or its per-user equivalent)
- **AND** the system SHALL include the returned pull requests in the queue data alongside review-requested and authored pull requests

#### Scenario: Complete reviewed results across multiple pages
- **WHEN** the reviewed search returns more pull requests than fit in a single result page
- **THEN** the system SHALL continue fetching subsequent pages until all reviewed pull requests are retrieved and SHALL return each pull request once with the same pull request id

#### Scenario: Page size and retry behavior are shared
- **WHEN** the system issues any page request for the reviewed search
- **THEN** the request SHALL fetch no more than 25 pull requests at a time
- **AND** a transient HTTP 5xx response SHALL be retried with backoff, up to two additional attempts, before reporting a refresh failure

#### Scenario: Reviewed fetch failure
- **WHEN** all retry attempts for the reviewed query fail
- **THEN** the system SHALL raise the error as a refresh failure and keep previously fetched queue data visible

#### Scenario: Reviewed search disabled
- **WHEN** `followup.include_reviewed` is set to `false`
- **THEN** the system SHALL NOT issue the reviewed search
