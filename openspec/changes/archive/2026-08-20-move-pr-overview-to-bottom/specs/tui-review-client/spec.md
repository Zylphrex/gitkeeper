## MODIFIED Requirements

### Requirement: Interactive PR Queue Navigation
The system SHALL provide a persistent single-queue interface listing all actionable pull requests in a flat list sorted by most recent activity (newest first), where every row is labeled with whether the next move is the user's, alongside a persistent overview section for the selected pull request.

#### Scenario: Navigate the activity-sorted pull request queue
- **WHEN** the TUI application loads
- **THEN** the system SHALL display the complete ordered list of actionable pull requests in the left panel sorted by last-updated time (newest first), then deterministically by repository name and pull request number
- **AND** each entry SHALL display an action badge as a single-character glyph marking the pull request state: `●` when awaiting the user's action, `○` when waiting on others, `◇` when waiting on its author, replacing the former tier badge and textual `wait: author` / `wait: others` / `awaiting you` badges
- **AND** each entry SHALL display the repository name and pull request number
- **AND** each entry SHALL display the pull request author alongside the repository name
- **AND** each entry SHALL display the pull request title on its own line beginning at the first column of the entry
- **AND** the title SHALL be truncated with a trailing ellipsis (`…`) when it exceeds the available row width, and SHALL NOT wrap, clip mid-word, or display scoring reason chips
- **AND** each entry SHALL render as exactly two rows total (one metadata row containing the action glyph, number, repository name, and author, followed by one title row), which SHALL hold regardless of how many entries the queue contains
- **AND** the metadata row SHALL NOT wrap: when the repository name, author, and action glyph do not fit within the available row width, the repository name SHALL be truncated with a trailing ellipsis (`…`) to fit
- **AND** the metadata row SHALL prefer leaving the author un-truncated when space is tight, truncating the repository name further before shortening the author
- **AND** the user SHALL be able to select and highlight different pull requests using Vim-style navigation keys (`j`/`k` for up/down, `gg`/`G` for top/bottom, `Ctrl+d`/`Ctrl+u` for paging), arrow keys, or mouse selection
- **AND** the pull request number in each entry SHALL be rendered as a clickable terminal hyperlink to the pull request URL when a URL is available

#### Scenario: Queue rows stay two rows tall when the list scrolls
- **WHEN** the queue contains more entries than fit in the pane, so that the list displays a vertical scrollbar
- **THEN** each entry SHALL still render as exactly two rows with the action glyph and author on the metadata row
- **AND** the title SHALL appear as a single truncated line on its own row rather than wrapping or being clipped

#### Scenario: Display selected PR overview and rationale
- **WHEN** a pull request is selected or clicked in the queue list
- **THEN** the system SHALL display the PR metadata, full description, a worded action-state line (awaiting the user's action, waiting on author, or waiting on others) and, when available, the reason chips that produced it (e.g., directly requested, re-review due, respond to review)
- **AND** the overview SHALL render in a fixed-height full-width row at the bottom of the interface, divided into two columns: the metadata and rationale on the left, and the PR description on the right
- **AND** the metadata SHALL be rendered in full: any metadata line that exceeds the left column width SHOULD wrap at the column edge and never be clipped or overflow off-screen
- **AND** the metadata SHALL include the repository, author, draft state, base and head branch refs, CI status, addition/deletion counts, changed file count, created date, relative time since last update, requested reviewers, a compact summary of existing reviews, and the latest author push time
- **AND** the metadata SHALL include a viewer-action status line stating what the current viewer has already done on the PR: never reviewed, approved, requested changes, or commented, including any inline comment count once diff threads are loaded and the relative time of the viewer's most recent action
- **AND** the viewer status SHALL indicate when a re-review is due because the author pushed after the viewer's last review
- **AND** the viewer status SHALL include the number of pending draft comments authored in the current session for that PR
- **AND** the metadata and rationale boxes SHALL size to their content within the fixed bottom-row height
- **AND** the description SHALL render as a non-scrollable preview showing as much of the description as fits the fixed bottom-right column, without a scrollbar or focus target
- **AND** the overview section SHALL remain visible while the user inspects the diff pane for the selected pull request
- **AND** the system SHALL synchronize the diff viewer with the newly selected pull request
- **AND** the pull request number in the overview header SHALL be rendered as a clickable terminal hyperlink to the pull request URL when a URL is available

#### Scenario: Overview is not a tab
- **WHEN** the TUI application loads
- **THEN** the overview section SHALL be visible in the fixed-height bottom row without requiring tab switching
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