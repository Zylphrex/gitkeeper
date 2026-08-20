## Purpose

Provides a full-screen interactive terminal interface (TUI) for navigating ranked pull request review queues, viewing diffs, leaving inline feedback, and submitting reviews.

## Requirements
### Requirement: Interactive PR Queue Navigation
The system SHALL provide a full-screen interactive interface listing all actionable pull requests in a single flat queue sorted by most recent activity (newest first) with keyboard and mouse navigation, where every row is labeled with whether the next move is the user's.

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
- **AND** the system SHALL NOT change the current selection, focus, or any in-progress draft comments

#### Scenario: Open selected PR with no URL
- **WHEN** the user presses the open-in-browser key (`o`) while the selected pull request has no URL
- **THEN** the system SHALL report that no URL is available for the pull request
- **AND** the system SHALL NOT attempt to open a browser

#### Scenario: Open selected PR with nothing selected
- **WHEN** the user presses the open-in-browser key (`o`) while no pull request is selected
- **THEN** the system SHALL report that no pull request is selected
- **AND** the system SHALL NOT attempt to open a browser
### Requirement: In-TUI Diff Viewer
The system SHALL provide an interactive diff viewer allowing users to inspect file changes and patches for the selected pull request directly within the terminal interface. The changed-files list SHALL render as a compact directory tree in which every row fits on a single line.

#### Scenario: View file diffs for a pull request
- **WHEN** the user switches to the diff view for a selected pull request
- **THEN** the system SHALL display the changed-files list and the syntax-highlighted unified diff of the selected file
- **AND** each file in the list SHALL be shown with its change-type indicator (added, modified, deleted, renamed)

#### Scenario: View compact file tree
- **WHEN** the changed-files list contains more than one file
- **THEN** the system SHALL group file entries under their respective directory headers as a tree
- **AND** directory header rows SHALL be non-navigable landmarks that the selection cursor skips over
- **AND** a directory containing a single child SHALL be flattened onto a single row instead of rendering a multi-line deep spine
- **AND** each file row SHALL display the file's name plus the least directory context needed to distinguish it, such that any row that would exceed the panel width SHALL be shortened rather than wrapped
- **AND** no row SHALL ever be rendered across multiple lines

#### Scenario: View file list with one path or no paths
- **WHEN** the changed-files list contains exactly one file
- **THEN** the system SHALL render that file without directory headers or wrapping
- **WHEN** the changed-files list contains no files
- **THEN** the system SHALL show an empty state indicator without wrapping or rendering directory artifacts

#### Scenario: Navigate through diff hunks and files
- **WHEN** inspecting a diff
- **THEN** the user SHALL be able to navigate between files and scroll through diff lines with Vim-style navigation keys (`j`/`k` for up/down lines, `gg`/`G` for top/bottom, `Ctrl+d`/`Ctrl+u` for paging) and arrow keys
- **AND** the user SHALL be able to switch focus between the file list and the diff viewer using `h`/`l`

#### Scenario: Search files within compact tree
- **WHEN** the user initiates a file search from the file list focus zone
- **THEN** the system SHALL filter the underlying file set by the search query
- **AND** the matching files SHALL be presented in the same compact tree form without wrapping
- **AND** each matched file SHALL remain selectable from the filtered list

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

### Requirement: Submit Pull Request Review
The system SHALL allow users to submit pull request reviews with an approval, change request, or general comment status including any authored inline comments. No single-key or other permissionless action SHALL submit a review; every review submission SHALL require the user to explicitly trigger and confirm submission.

#### Scenario: Submit review approval
- **WHEN** the user triggers the approve review action and confirms submission
- **THEN** the system SHALL submit the review mutation to GitHub with an APPROVE decision and clear the reviewed PR or update its status

#### Scenario: Submit review with requested changes
- **WHEN** the user triggers the request changes action, enters required feedback, and confirms
- **THEN** the system SHALL submit the review mutation to GitHub with a REQUEST_CHANGES decision and include all pending comments

#### Scenario: Approve requires confirmation
- **WHEN** the user has not explicitly confirmed an approval submission
- **THEN** the system SHALL NOT submit an APPROVE review to GitHub

### Requirement: Manual Queue Refresh
The system SHALL provide a manual refresh trigger to re-query GitHub and re-score the queue on demand while providing non-blocking visual progress feedback.

#### Scenario: Trigger manual refresh
- **WHEN** the user presses the refresh key
- **THEN** the system SHALL trigger asynchronous background fetching from GitHub and relevance re-scoring
- **AND** the system SHALL display the current background activity stage in the top header without blocking queue navigation
- **AND** the system SHALL update the last refreshed timestamp upon completion

#### Scenario: Handle refresh errors gracefully
- **WHEN** a background refresh operation fails
- **THEN** the system SHALL report the failure in the status display
- **AND** the system SHALL keep existing queue items visible and interactive

### Requirement: Top Header Status and Refresh Tracking
The system SHALL display an application header indicating active background tasks and the timestamp of the last successful queue refresh.

#### Scenario: Display idle state with last refreshed timestamp
- **WHEN** no background network or scoring operations are active
- **THEN** the header SHALL show the last refreshed time (or initial status if no refresh has completed)

#### Scenario: Display active background operation
- **WHEN** a queue refresh or initial fetch is executing in the background
- **THEN** the header SHALL display an active status message describing the current stage (e.g. fetching GitHub data or scoring relevance)
- **AND** the message SHALL lead with an animated spinner that cycles through frames while the operation is active

### Requirement: Diff View Asynchronous Loading State
The system SHALL provide explicit visual loading indicators in the diff viewer when fetching patches asynchronously.

#### Scenario: Display loading state while fetching diff
- **WHEN** a pull request is selected whose diff is not currently cached
- **THEN** the diff view SHALL display a loading indicator until the patch data is retrieved and rendered
- **AND** the loading indicator SHALL animate while the patch is being fetched

#### Scenario: Display error state on diff fetch failure
- **WHEN** fetching a pull request patch fails
- **THEN** the diff view SHALL display a clear error message explaining the failure
- **AND** the loading indicator SHALL stop animating

### Requirement: Hide Whitespace in Diff View
The system SHALL provide a review-tunable diff mode that hides whitespace-only differences by comparing changed lines with whitespace ignored (the same comparison `git diff -w` uses), so that a line pair differing only in whitespace SHALL be rendered as unchanged context instead of an added/deleted change pair, and a hunk whose differences collapse entirely to whitespace SHALL be dropped from the displayed diff. The mode SHALL NOT alter any change lines that differ beyond whitespace, and the mode SHALL be session-scoped (not persisted to config).

The reviewer SHALL be able to toggle the mode on and off while reviewing, and the system SHALL show a clear active-mode indicator within the diff view so a reviewer is never silently looking at a filtered diff.

#### Scenario: Toggle whitespace hiding with the w key

- **WHEN** the reviewer presses the toggle key (`w`) while the diff view is loaded
- **THEN** the system SHALL invert the whitespace-hiding mode
- **AND** the system SHALL re-render the currently displayed pull request's diff from the cached diff text without refetching from GitHub

#### Scenario: A line that differs only in whitespace is hidden

- **WHEN** whitespace-hiding mode is active AND a deleted line and an added line in the same hunk are equal once all whitespace is removed
- **THEN** the system SHALL render that content as a single context line (no addition or deletion prefix) rather than a `-`/`+` change pair
- **AND** the context line SHALL carry the correct new-file and old-file line numbers

#### Scenario: A hunk that collapses is dropped

- **WHEN** whitespace-hiding mode is active AND every change line in a hunk belongs to a whitespace-only pair
- **THEN** the system SHALL drop that hunk from the rendered diff

#### Scenario: Non-whitespace changes are unaffected

- **WHEN** whitespace-hiding mode is active AND a hunk contains change lines that differ beyond whitespace
- **THEN** the system SHALL keep those change pairs rendered exactly as they would be in the default mode, and any whitespace-only pairs within the same hunk SHALL still be collapsed to context

#### Scenario: Mode defaults to off per session

- **WHEN** the TUI application starts
- **THEN** the whitespace-hiding mode SHALL be disabled
- **AND** the diff SHALL render with all whitespace-only changes visible until the reviewer toggles the mode

#### Scenario: Active mode is indicated

- **WHEN** whitespace-hiding mode is active
- **THEN** the diff view SHALL display a visible indicator (e.g. a header label or footer key hint) that the mode is on
- **AND** the indicator SHALL disappear or revert when the mode is toggled off
