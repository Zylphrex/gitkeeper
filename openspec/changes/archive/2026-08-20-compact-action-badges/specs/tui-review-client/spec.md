## MODIFIED Requirements

### Requirement: Interactive PR Queue Navigation
The system SHALL provide a full-screen interactive interface listing all actionable pull requests in a single flat queue sorted by most recent activity (newest first) with keyboard and mouse navigation, where every row is labeled with whether the next move is the user's.

#### Scenario: Navigate the activity-sorted pull request queue
- **WHEN** the TUI application loads
- **THEN** the system SHALL display the complete ordered list of actionable pull requests in the left panel sorted by last-updated time (newest first), then deterministically by repository name and pull request number
- **AND** each entry SHALL display an action badge as a single-character glyph marking the pull request state: `●` when awaiting the user's action, `○` when waiting on others, `◇` when waiting on its author (replacing the former textual `wait: author` / `wait: others` badges and the former `awaiting you` badge)
- **AND** each entry SHALL display the repository name and pull request number
- **AND** each entry SHALL display the pull request author alongside the repository name
- **AND** each entry SHALL display the pull request title on its own line beginning at the first column of the entry
- **AND** the title SHALL be truncated with a trailing ellipsis (`…`) when it exceeds the available row width, and SHALL NOT wrap, clip mid-word, or display scoring reason chips
- **AND** each entry SHALL render as exactly two rows total (one metadata row containing the action glyph, number, repository name, and author, followed by one title row), which SHALL hold regardless of how many entries the queue contains
- **AND** the metadata row SHALL NOT wrap: when the repository name, author, and action glyph do not fit within the available row width, the repository name SHALL be truncated with a trailing ellipsis (`…`) to fit
- **AND** the metadata row SHALL prefer leaving the author un-truncated when space is tight, truncating the repository name further before shortening the author
- **AND** the available row width used for truncation SHALL account for any vertical scrollbar shown by the list, so that truncation limits never exceed the width at which entries are actually rendered
- **AND** the user SHALL be able to select and highlight different pull requests using Vim-style navigation keys (`j`/`k` for up/down, `gg`/`G` for top/bottom, `Ctrl+d`/`Ctrl+u` for paging), arrow keys, or mouse selection
- **AND** the pull request number in each entry SHALL be rendered as a clickable terminal hyperlink to the pull request URL when a URL is available

#### Scenario: Queue entries remain two rows when the list scrolls
- **WHEN** the queue contains more entries than fit in the pane, so that the list displays a vertical scrollbar
- **THEN** each entry SHALL still render as exactly two rows with the action glyph and author on the metadata row
- **AND** the title SHALL appear as a single truncated line on its own row rather than wrapping or being clipped

#### Scenario: Display selected PR overview and rationale
- **WHEN** a pull request is selected or clicked in the queue list
- **THEN** the system SHALL display the PR metadata, full description, a worded action-state line (awaiting the user's action, waiting on author, or waiting on others) and, when available, the reason chips that produced it (e.g., directly requested, re-review due, respond to review)
