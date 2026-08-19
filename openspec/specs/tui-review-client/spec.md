## Purpose

Provides a full-screen interactive terminal interface (TUI) for navigating ranked pull request review queues, viewing diffs, leaving inline feedback, and submitting reviews.

## Requirements
### Requirement: Interactive PR Queue Navigation
The system SHALL provide a full-screen interactive interface listing actionable pull requests in a singular continuous list sorted from highest to lowest triage tier with keyboard and mouse navigation.

#### Scenario: Navigate the triaged pull request queue
- **WHEN** the TUI application loads
- **THEN** the system SHALL display the complete ordered list of actionable pull requests in the left panel sorted by triage tier (top tier first), then by author activity heat (hottest first), then by review size (smallest first), then deterministically
- **AND** each entry SHALL display its triage tier label, repository name, and pull request number instead of a numeric composite score
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
### Requirement: In-TUI Diff Viewer
The system SHALL provide an interactive diff viewer allowing users to inspect file changes and patches for the selected pull request directly within the terminal interface.

#### Scenario: View file diffs for a pull request
- **WHEN** the user switches to the diff view for a selected pull request
- **THEN** the system SHALL display the list of modified files and the syntax-highlighted unified diff of the selected file

#### Scenario: Navigate through diff hunks and files
- **WHEN** inspecting a diff
- **THEN** the user SHALL be able to navigate between files and scroll through diff lines with Vim-style navigation keys (`j`/`k` for up/down lines, `gg`/`G` for top/bottom, `Ctrl+d`/`Ctrl+u` for paging) and arrow keys
- **AND** the user SHALL be able to switch focus between the file list and the diff viewer using `h`/`l`

### Requirement: Inline and Top-Level Commenting
The system SHALL allow users to author inline review comments on specific diff lines as well as top-level review comments from within the interface.

The system SHALL reliably route the inline comment action to the inline comment input dialog for the currently selected diff line, so that the dialog SHALL open whenever the user triggers the comment action while a diff line is selected, regardless of message dispatch naming conventions in the UI framework.

#### Scenario: Add inline comment on a diff line
- **WHEN** the user selects a specific line in the diff view and triggers the comment action
- **THEN** the system SHALL open an input dialog allowing the user to enter markdown feedback
- **AND** the dialog SHALL open immediately for the selected file and line without requiring any extra step
- **AND** attach the pending comment to that file and line number
- **AND** make the pending comment available for inclusion in a subsequent review submission

### Requirement: Submit Pull Request Review
The system SHALL allow users to submit pull request reviews with an approval, change request, or general comment status including any authored inline comments.

#### Scenario: Submit review approval
- **WHEN** the user triggers the approve review action and confirms submission
- **THEN** the system SHALL submit the review mutation to GitHub with an APPROVE decision and clear the reviewed PR or update its status

#### Scenario: Submit review with requested changes
- **WHEN** the user triggers the request changes action, enters required feedback, and confirms
- **THEN** the system SHALL submit the review mutation to GitHub with a REQUEST_CHANGES decision and include all pending comments

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
