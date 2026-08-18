## Purpose

Assigns each actionable pull request a bounded triage tier and a deterministic ordering, so reviewers see pressure bands ("do now," "on you," "this week," "whenever") instead of trusting a flat composite number.

## ADDED Requirements

### Requirement: Assign Triage Tier
The system SHALL assign exactly one of four tiers (_T0_, _T1_, _T2_, _T3_) to each actionable pull request based on assignment type, reviewer verdict pressure, local git affinity, and author activity. The composite numeric score SHALL NOT determine queue ordering.

#### Scenario: You are the bottleneck
- **WHEN** the user is a directly requested reviewer AND every other requested reviewer has already submitted a review verdict (approved, dismissed, or requested changes) OR the user is the only requested reviewer
- **THEN** the pull request SHALL be assigned the top tier, _T0_

#### Scenario: Directly requested
- **WHEN** the user is a directly requested reviewer but other requested reviewers have not yet all submitted verdicts
- **THEN** the pull request SHALL be assigned to _T1_

#### Scenario: Author is actively pushing
- **WHEN** the pull request's latest commit or push activity is within the configured hotness window
- **THEN** the pull request SHALL be assigned to _T1_ as a hot item

#### Scenario: Re-review is due
- **WHEN** the user has previously submitted a review verdict AND the author has pushed new commit activity after that verdict
- **THEN** the pull request SHALL be assigned to _T1_ and flagged as a re-review

#### Scenario: Team-requested with local affinity
- **WHEN** the pull request is requested via a team alias the user belongs to AND the user has touched a meaningful portion of the changed files within the git lookback window
- **THEN** the pull request SHALL be assigned to _T2_

#### Scenario: Everything else actionable
- **WHEN** the pull request is actionable but does not match any higher-tier rule
- **THEN** it SHALL be assigned to the lowest visible tier, _T3_

### Requirement: Order Triage Queue
The system SHALL sort actionable pull requests by tier, then heat, then review effort, with deterministic tie-breaking, and SHALL NOT discard any actionable pull request based on a numeric score threshold.

#### Scenario: Order by heat within tier
- **WHEN** multiple actionable pull requests share the same tier
- **THEN** the system SHALL sort them by most recent author push/activity first, then by smallest diff size, then deterministically by repository name and pull request number

#### Scenario: Never rank below a team ask
- **WHEN** a pull request directly requests the user's review AND another pull request is only team-assigned
- **THEN** the directly requested pull request SHALL be ordered before the team-assigned one regardless of local affinity or diff size