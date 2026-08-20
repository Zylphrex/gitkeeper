## MODIFIED Requirements

### Requirement: Configure Follow-up Tracking
The system SHALL expose a `followup` configuration block controlling whether the user's authored and reviewed pull requests are collected in the queue, with defaults that keep the features enabled. The block SHALL NOT expose settings for hiding waiting states or for a staleness threshold.

#### Scenario: Enable or disable authored pull request collection
- **WHEN** `followup.include_authored` is set to `true` (the default)
- **THEN** the system SHALL fetch the user's authored open pull requests alongside review-requested pull requests
- **WHEN** `followup.include_authored` is set to `false`
- **THEN** the system SHALL NOT fetch the user's authored pull requests

#### Scenario: Enable or disable reviewed pull request collection
- **WHEN** `followup.include_reviewed` is set to `true` (the default)
- **THEN** the system SHALL fetch the user's reviewed open pull requests alongside review-requested and authored pull requests
- **WHEN** `followup.include_reviewed` is set to `false`
- **THEN** the system SHALL NOT fetch the user's reviewed pull requests

#### Scenario: Warn on removed follow-up keys
- **WHEN** a config file still defines `followup.show_waiting_on_author`, `followup.show_waiting_on_others`, or `followup.staleness_warn_after_days`
- **THEN** the system SHALL log a deprecation warning naming the key
- **AND** the system SHALL ignore the removed keys instead of applying them
