## ADDED Requirements

### Requirement: Configure Follow-up Tracking
The system SHALL expose a `followup` configuration block controlling whether authored pull requests are collected, which waiting bands are displayed, and after how many days an outstanding follow-up is flagged as stale, with defaults that keep the feature enabled.

#### Scenario: Enable authored pull request collection
- **WHEN** `followup.include_authored` is set to `true` (the default)
- **THEN** the system SHALL fetch the user's authored open pull requests alongside review-requested pull requests
- **WHEN** `followup.include_authored` is set to `false`
- **THEN** the system SHALL NOT fetch the user's authored pull requests

#### Scenario: Show or hide the waiting-on-author band
- **WHEN** `followup.show_waiting_on_author` is set to `true` (the default)
- **THEN** pull requests waiting on the author SHALL be rendered in the waiting band
- **WHEN** `followup.show_waiting_on_author` is set to `false`
- **THEN** waiting-on-author pull requests SHALL NOT be displayed in any band

#### Scenario: Show or hide the waiting-on-others band
- **WHEN** `followup.show_waiting_on_others` is set to `true` (the default)
- **THEN** pull requests waiting on other reviewers, CI, or merge SHALL be rendered in the waiting band
- **WHEN** `followup.show_waiting_on_others` is set to `false`
- **THEN** waiting-on-others pull requests SHALL NOT be displayed in any band

#### Scenario: Configure the staleness threshold
- **WHEN** `followup.staleness_warn_after_days` is set to a number of days (default `3`)
- **THEN** the system SHALL flag active-band follow-ups outstanding beyond that threshold with a staleness indicator