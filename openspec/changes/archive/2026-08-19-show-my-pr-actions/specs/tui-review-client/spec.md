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
- **AND** each entry SHALL render as exactly two rows total (one metadata row containing tier label, number, repository name, and author, followed by one title row), which SHALL hold regardless of how many entries the queue contains
- **AND** the metadata row SHALL NOT wrap: when the repository name and author do not fit within the available row width, the repository name SHALL be truncated with a trailing ellipsis (`…`) to fit
- **AND** the available row width used for truncation SHALL account for any vertical scrollbar shown by the list, so that truncation limits never exceed the width at which entries are actually rendered
- **AND** the user SHALL be able to select and highlight different pull requests using Vim-style navigation keys (`j`/`k` for up/down, `gg`/`G` for top/bottom, `Ctrl+d`/`Ctrl+u` for paging), arrow keys, or mouse selection
- **AND** the pull request number in each entry SHALL be rendered as a clickable terminal hyperlink to the pull request URL when a URL is available

#### Scenario: Queue entries remain two rows when the list scrolls
- **WHEN** the queue contains more entries than fit in the pane, so that the list displays a vertical scrollbar
- **THEN** each entry SHALL still render as exactly two rows with the author on the metadata row
- **AND** the title SHALL appear as a single truncated line on its own row rather than wrapping or being clipped

#### Scenario: Display selected PR overview and rationale
- **WHEN** a pull request is selected or clicked in the queue list
- **THEN** the system SHALL display the PR metadata, full description, and a triage rationale consisting of the tier label and the specific reason chips that produced it (e.g., bottleneck, direct request, author activity, re-review, wait time, affinity)
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

#### Scenario: Open selected PR in the web browser
- **WHEN** the user presses the open-in-browser key (`o`) while a pull request is selected and a URL is available
- **THEN** the system SHALL open the selected pull request's GitHub URL in the default web browser
- **AND** the system SHALL NOT change the current selection, focus, or any in-progress comment drafts

#### Scenario: Open selected PR with no URL
- **WHEN** the user presses the open-in-browser key (`o`) while the selected pull request has no URL
- **THEN** the system SHALL report that no URL is available for the pull request
- **AND** the system SHALL NOT attempt to open a browser

#### Scenario: Open selected PR with nothing selected
- **WHEN** the user presses the open-in-browser key (`o`) while no pull request is selected
- **THEN** the system SHALL report that no pull request is selected
- **AND** the system SHALL NOT attempt to open a browser

### Requirement: Inline and Top-Level Commenting
The system SHALL allow users to author inline review comments on specific diff lines as well as top-level review comments from within the interface.

The system SHALL reliably route the inline comment action to the inline comment input dialog for the currently selected diff line, so that the dialog SHALL open whenever the user triggers the comment action while a diff line is selected, regardless of message dispatch naming conventions in the UI framework.

The system SHALL display existing review threads when a pull request's diff is viewed: each thread SHALL appear attached to its file and diff line alongside the diff content, labeled with the thread author, and visually distinct from the reviewer's own pending comments.

#### Scenario: Add inline comment on a diff line
- **WHEN** the user selects a specific line in the diff view and triggers the comment action
- **THEN** the system SHALL open an input dialog allowing the user to enter markdown feedback
- **AND** the dialog SHALL open immediately for the selected file and line without requiring any extra step
- **AND** attach the pending comment to that file and line number
- **AND** make the pending comment available for inclusion in a subsequent review submission

#### Scenario: View existing review threads on a diff
- **WHEN** the user views the diff of a pull request that has existing review threads
- **THEN** the system SHALL display each review thread on the diff line it refers to
- **AND** each displayed thread SHALL identify its author
- **AND** each displayed thread SHALL be visually distinct from pending comments
- **AND** a thread authored by the current viewer SHALL be visually distinct from threads authored by other reviewers
- **AND** threads whose target line cannot be matched to a rendered diff line SHALL NOT be displayed

#### Scenario: Existing threads and pending comment on the same line
- **WHEN** a diff line has both existing review threads and a pending comment authored by the reviewer
- **THEN** the system SHALL display the existing threads and the pending comment together on that line
- **AND** the pending comment SHALL remain visually distinct from the existing threads

#### Scenario: Thread fetch fails while viewing a diff
- **WHEN** fetching existing review threads for a pull request fails
- **THEN** the diff SHALL still be displayed and navigable
- **AND** the system SHALL report the thread fetch failure in the status display