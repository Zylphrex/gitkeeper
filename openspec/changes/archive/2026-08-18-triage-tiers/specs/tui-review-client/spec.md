## MODIFIED Requirements

### Requirement: Interactive PR Queue Navigation
The system SHALL provide a full-screen interactive interface listing actionable pull requests in a singular continuous list sorted from highest to lowest triage tier with keyboard and mouse navigation.

#### Scenario: Navigate the triaged pull request queue
- **WHEN** the TUI application loads
- **THEN** the system SHALL display the complete ordered list of actionable pull requests in the left panel sorted by triage tier (top tier first), then by author activity heat (hottest first), then by review size (smallest first), then deterministically
- **AND** each entry SHALL display its triage tier label, repository name, and pull request number instead of a numeric composite score
- **AND** the user SHALL be able to select and highlight different pull requests using Vim-style navigation keys (`j`/`k` for up/down, `gg`/`G` for top/bottom, `Ctrl+d`/`Ctrl+u` for paging), arrow keys, or mouse selection

#### Scenario: Display selected PR overview and rationale
- **WHEN** a pull request is selected or clicked in the queue list
- **THEN** the system SHALL display the PR metadata, full description, and a triage rationale consisting of the tier label and the specific reason chips that produced it (e.g., bottleneck, direct request, author activity, re-review, wait time, affinity)
- **AND** the metadata SHALL be rendered in full: any metadata line that exceeds the overview panel width SHOULD wrap at the panel edge and never be clipped or overflow off-screen
- **AND** the metadata SHALL include the repository, author, draft state, base and head branch refs, CI status, addition/deletion counts, changed file count, created date, relative time since last update, requested reviewers, a compact summary of existing reviews, and the latest author push time
- **AND** the metadata and rationale boxes SHALL size to their content so the PR body retains the remaining panel height
- **AND** the overview section SHALL remain visible while the user inspects the Files & Diff pane for the selected pull request
- **AND** the system SHALL synchronize the diff viewer with the newly selected pull request

#### Scenario: Overview is not a tab
- **WHEN** the TUI application loads with the Files & Diff pane active
- **THEN** the overview section SHALL be visible on the far right without requiring tab switching
- **AND** the overview section SHALL NOT be selectable as a tab