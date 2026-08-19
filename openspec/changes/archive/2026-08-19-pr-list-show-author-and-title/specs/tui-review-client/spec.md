## MODIFIED Requirements

### Requirement: Interactive PR Queue Navigation
The system SHALL provide a full-screen interactive interface listing actionable pull requests in a singular continuous list sorted from highest to lowest triage tier with keyboard and mouse navigation.

#### Scenario: Navigate the triaged pull request queue
- **WHEN** the TUI application loads
- **THEN** the system SHALL display the complete ordered list of actionable pull requests in the left panel sorted by triage tier (top tier first), then by author activity heat (hottest first), then by review size (smallest first), then deterministically
- **AND** each entry SHALL display its triage tier label, repository name, and pull request number instead of a numeric composite score
- **AND** each entry SHALL display the pull request author alongside the repository name
- **AND** each entry SHALL display the pull request title on its own line beginning at the first column of the entry
- **AND** the title SHALL be truncated with a trailing ellipsis (`…`) when it exceeds the available row width, and SHALL NOT wrap, clip mid-word, or display scoring reason chips
- **AND** the user SHALL be able to select and highlight different pull requests using Vim-style navigation keys (`j`/`k` for up/down, `gg`/`G` for top/bottom, `Ctrl+d`/`Ctrl+u` for paging), arrow keys, or mouse selection
- **AND** the pull request number in each entry SHALL be rendered as a clickable terminal hyperlink to the pull request URL when a URL is available

#### Scenario: Display selected PR overview and rationale
- **WHEN** a pull request is selected or clicked in the queue list
- **THEN** the system SHALL display the PR metadata, full description, and a triage rationale consisting of the tier label and the specific reason chips that produced it (e.g., bottleneck, direct request, author activity, re-review, wait time, affinity)
- **AND** the metadata SHALL be rendered in full: any metadata line that exceeds the overview panel width SHOULD wrap at the panel edge and never be clipped or overflow off-screen
- **AND** the metadata SHALL include the repository, author, draft state, base and head branch refs, CI status, addition/deletion counts, changed file count, created date, relative time since last update, requested reviewers, a compact summary of existing reviews, and the latest author push time
- **AND** the metadata and rationale boxes SHALL size to their content so the PR body retains the remaining panel height
- **AND** the overview section SHALL remain visible while the user inspects the diff pane for the selected pull request
- **AND** the system SHALL synchronize the diff viewer with the newly selected pull request
- **AND** the pull request number in the overview header SHALL be rendered as a clickable terminal hyperlink to the pull request URL when a URL is available

#### Scenario: Overview is not a tab
- **WHEN** the TUI application loads
- **THEN** the overview section SHALL be visible on the far right without requiring tab switching
- **AND** the overview section SHALL NOT be selectable as a tab
- **AND** the diff pane SHALL be rendered as a plain, always-visible pane without a labeled tab bar
- **AND** the system SHALL NOT provide a dedicated keyboard shortcut for switching to the diff pane

#### Scenario: Open selected PR in the web browser
- **WHEN** the user presses the open-in-browser key (`o`) while a pull request is selected and a URL is available
- **THEN** the system SHALL open the selected pull request's GitHub URL in the default web browser
- **AND** the system SHALL NOT change the current selection, focus, or any in-progress draft comments

#### Scenario: Open selected PR with no URL
- **WHEN** the user presses the open-in-browser key (`o`) while the selected pull request has no URL
- **THEN** the system SHALL report that no URL is available for the pull request
- **AND** the system SHALL NOT attempt to open a browser

#### Scenario: Open selected PR with nothing selected
- **WHEN** the user presses the open-in-browser key (`o`) while no pull request is selected
- **THEN** the system SHALL report that no pull request is selected
- **AND** the system SHALL NOT attempt to open a browser