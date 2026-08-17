## Purpose

Evaluates pull requests against actionability filters, local git affinity scores, assignment types, and urgency heuristics to compute a composite relevance score.

## ADDED Requirements

### Requirement: Actionability Gating
The system SHALL filter out pull requests that are not currently ready or actionable for the user to review.

#### Scenario: Filter draft pull requests
- **WHEN** a pull request has draft status set to true and `ignore_drafts` is enabled
- **THEN** the system SHALL exclude the pull request from the actionable review queue

#### Scenario: Filter already reviewed pull requests
- **WHEN** the user has already submitted an approved or changes-requested review for the latest commit
- **THEN** the system SHALL exclude the pull request from the actionable review queue

### Requirement: Calculate Affinity and Urgency Score
The system SHALL compute a composite relevance score between 0 and 100 for each actionable pull request based on local git context, assignment type, and PR characteristics.

#### Scenario: Calculate composite score for direct review on familiar code
- **WHEN** a user is directly requested on a PR where they authored recent commits on touched files
- **THEN** the system SHALL calculate an affinity score reflecting file touch recency and an assignment bonus, resulting in a high composite score

#### Scenario: Calculate composite score for team broadcast on unfamiliar code
- **WHEN** a PR is assigned via a team alias and the user has no commit history on the touched files
- **THEN** the system SHALL assign base team points with low affinity points, ranking it below high-context PRs

#### Scenario: Small PR urgency boost
- **WHEN** a pull request touches fewer than 100 lines of code
- **THEN** the system SHALL apply an urgency/size bonus to encourage fast turnarounds
