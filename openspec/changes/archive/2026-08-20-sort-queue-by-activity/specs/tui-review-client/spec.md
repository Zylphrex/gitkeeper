## MODIFIED Requirements

### Requirement: Interactive PR Queue Navigation
The system SHALL provide a full-screen interactive interface listing all actionable pull requests in a single flat queue sorted by most recent activity (newest first) with keyboard and mouse navigation, where every row is labeled with whether the next move is the user's.

#### Scenario: Navigate the activity-sorted pull request queue
- **WHEN** the TUI application loads
- **THEN** the system SHALL display the complete ordered list of actionable pull requests in the left panel sorted by last-updated time (newest first), then deterministically by repository name and pull request number
- **AND** each entry SHALL display an action badge stating whether the pull request is awaiting the user's action or is waiting on its author (`wait: author`) or others (`wait: others`), replacing the former tier badge
- **AND** each entry SHALL display the repository name and pull request number
- **AND** each entry SHALL display the pull request author alongside the repository name
- **AND** each entry SHALL display the pull request title on its own line beginning at the first column of the entry
- **AND** the title SHALL be truncated with a trailing ellipsis (`…`) when it exceeds the available row width, and SHALL NOT wrap, clip mid-word, or display scoring reason chips
- **AND** each entry SHALL render as exactly two rows total (one metadata row containing the action badge, number, repository name, and author, followed by one title row), which SHALL hold regardless of how many entries the queue contains
- **AND** the metadata row SHALL NOT wrap: when the repository name, author, and badge do not fit within the available row width, the repository name SHALL be truncated with a trailing ellipsis (`…`) to fit
- **AND** the available row width used for truncation SHALL account for any vertical scrollbar shown by the list, so that truncation limits never exceed the width at which entries are actually rendered
- **AND** the user SHALL be able to select and highlight different pull requests using Vim-style navigation keys (`j`/`k` for up/down, `gg`/`G` for top/bottom, `Ctrl+d`/`Ctrl+u` for paging), arrow keys, or mouse selection
- **AND** the pull request number in each entry SHALL be rendered as a clickable terminal hyperlink to the pull request URL when a URL is available

#### Scenario: Queue entries remain two rows when the list scrolls
- **WHEN** the queue contains more entries than fit in the pane, so that the list displays a vertical scrollbar
- **THEN** each entry SHALL still render as exactly two rows with the action badge and author on the metadata row
- **AND** the title SHALL appear as a single truncated line on its own row rather than wrapping or being clipped

#### Scenario: Display selected PR overview and rationale
- **WHEN** a pull request is selected or clicked in the queue list
- **THEN** the system SHALL display the PR metadata, full description, an action-state line (awaiting the user's action, waiting on author, or waiting on others) and, when available, the reason chips that produced it (e.g., directly requested, re-re-review due, respond to review)
- **AND** the metadata SHALL be rendered in full: any metadata line that exceeds the overview panel width SHOULD wrap at the panel edge and never be clipped or overflow off-screen
- **AND** the metadata SHALL include the repository, author, draft state, base and head branch refs, CI status, addition/deletion counts, changed file count, created date, relative time since last update, requested reviewers, a compact summary of existing reviews, and the latest author push time
- **AND** the metadata SHALL include a viewer-action status line stating what the current viewer has already done on the PR: never reviewed, approved, requested changes, or commented, including any inline comment count once diff threads are loaded and the relative time of the viewer's most recent action
- **AND** the viewer status SHALL indicate when a re-review is due because the author pushed after the viewer's last review
- **AND** the viewer status SHALL include the number of pending draft comments authored in the current session for that PR
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

## REMOVED Requirements

### Requirement: Render the Waiting Band
**Reason**: The waiting band is removed from the UI; all actionable pull requests form a single flat recency-ordered queue, and waiting-on-author and waiting-on-others pull requests are labeled by their turn state instead of being rendered in a separated, dimmed section.
**Migration**: Remove the waiting band separator and the dimmed waiting section; each row's action badge conveys whether the next move belongs to the user, the author, or others.

### Requirement: Display Staleness on Active Follow-up Labels
**Reason**: The staleness marker (`[Kd]` on rows) is removed; recency ordering replaces the need to decorate stale rows, so no staleness decoration remains in the list.
**Migration**: Stop computing and rendering staleness markers in the entry rows; remove the staleness configuration key.