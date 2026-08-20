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
The system SHALL expose a `followup` configuration block controlling whether the user's authored pull requests are collected in the queue, with defaults that keep the feature enabled. The block SHALL NOT expose settings for hiding waiting states or for a staleness threshold.

#### Scenario: Enable or disable authored pull request collection
- **WHEN** `followup.include_authored` is set to `true` (the default)
- **THEN** the system SHALL fetch the user's authored open pull requests alongside review-requested pull requests
- **WHEN** `followup.include_authored` is set to `false`
- **THEN** the system SHALL NOT fetch the user's authored pull requests

#### Scenario: Warn on removed follow-up keys
- **WHEN** a config file still defines `followup.show_waiting_on_author`, `followup.show_waiting_on_others`, or `followup.staleness_warn_after_days`
- **THEN** the system SHALL log a deprecation warning naming the key
- **AND** the system SHALL ignore the removed keys instead of applying them
