## Purpose

Provides persistent configuration management for user credentials, repository path locations, scoring heuristic thresholds, and CLI preferences.

## Requirements

### Requirement: Load and Parse User Configuration
The system SHALL load configuration from user-level and repository-level configuration files, supporting environment variable expansion for sensitive fields.

#### Scenario: Load valid global configuration
- **WHEN** the user runs a command and `~/.config/gitkeeper/config.yaml` exists
- **THEN** the system SHALL parse the configuration settings and expand environment variables like `${GITHUB_TOKEN}`

#### Scenario: Fallback when configuration file is missing
- **WHEN** no configuration file exists at standard paths
- **THEN** the system SHALL apply sensible defaults and use environment variables (e.g. `GITHUB_TOKEN`) if present

### Requirement: Repository Path Mapping and Auto-Discovery
The system SHALL resolve local filesystem paths for GitHub repositories using explicit mappings or directory auto-discovery.

#### Scenario: Explicit repository path mapping
- **WHEN** a repository `owner/name` matches an explicit entry in `repositories.mapping`
- **THEN** the system SHALL resolve the repository to the specified local path

#### Scenario: Auto-discovery of local repository clones
- **WHEN** `repositories.auto_discover_dir` is configured and a repository is not in explicit mappings
- **THEN** the system SHALL search the directory for local git clones matching the remote GitHub repository URL

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
