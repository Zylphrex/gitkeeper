## Purpose

Inspects local git repository clones to determine commit history, author familiarity, and path touch frequency for modified files.

## Requirements

### Requirement: Inspect Local Commit History for Paths
The system SHALL query the local git history of a cloned repository to evaluate author activity on specific file paths within a configured lookback window.

#### Scenario: User has recent commits on touched files
- **WHEN** evaluating a list of file paths against local git history and the user authored commits within the lookback window
- **THEN** the system SHALL compute touch counts and the recency of the latest commit for each file

#### Scenario: File paths not found or no commits by user
- **WHEN** the user has authored zero commits for the specified paths within the lookback window
- **THEN** the system SHALL return zero touch count and no recent activity for those paths

### Requirement: Missing Local Clone Graceful Degradation
The system SHALL handle scenarios where a local clone for a repository is not available on disk.

#### Scenario: Local clone not found
- **WHEN** a pull request belongs to a repository with no corresponding local clone on the filesystem
- **THEN** the system SHALL flag the repository as uninspected and return neutral/fallback affinity scores without throwing an unhandled exception
