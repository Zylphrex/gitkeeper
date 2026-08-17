## Purpose

Provides a full-screen interactive terminal interface (TUI) for navigating ranked pull request review queues, viewing diffs, leaving inline feedback, and submitting reviews.

## Requirements

### Requirement: Interactive PR Queue Navigation
The system SHALL provide a full-screen interactive interface listing actionable pull requests ranked by relevance score with keyboard navigation.

#### Scenario: Navigate ranked pull requests
- **WHEN** the TUI application loads
- **THEN** the system SHALL display the ranked list of pull requests in the left panel with relevance scores, repository names, and authors
- **AND** the user SHALL be able to select and highlight different pull requests using keyboard navigation (e.g. arrow keys or j/k)

#### Scenario: Display selected PR overview and rationale
- **WHEN** a pull request is selected in the queue
- **THEN** the system SHALL display the PR metadata, full description, and detailed scoring rationale breakdown in the right overview panel

### Requirement: In-TUI Diff Viewer
The system SHALL provide an interactive diff viewer allowing users to inspect file changes and patches for the selected pull request directly within the terminal interface.

#### Scenario: View file diffs for a pull request
- **WHEN** the user switches to the diff view for a selected pull request
- **THEN** the system SHALL display the list of modified files and the syntax-highlighted unified diff of the selected file

#### Scenario: Navigate through diff hunks and files
- **WHEN** inspecting a diff
- **THEN** the user SHALL be able to navigate between files and scroll through diff lines with keyboard controls

### Requirement: Inline and Top-Level Commenting
The system SHALL allow users to author inline review comments on specific diff lines as well as top-level review comments from within the interface.

#### Scenario: Add inline comment on a diff line
- **WHEN** the user selects a specific line in the diff view and triggers the comment action
- **THEN** the system SHALL open an input dialog allowing the user to enter markdown feedback
- **AND** attach the pending comment to that file and line number

### Requirement: Submit Pull Request Review
The system SHALL allow users to submit pull request reviews with an approval, change request, or general comment status including any authored inline comments.

#### Scenario: Submit review approval
- **WHEN** the user triggers the approve review action and confirms submission
- **THEN** the system SHALL submit the review mutation to GitHub with an APPROVE decision and clear the reviewed PR or update its status

#### Scenario: Submit review with requested changes
- **WHEN** the user triggers the request changes action, enters required feedback, and confirms
- **THEN** the system SHALL submit the review mutation to GitHub with a REQUEST_CHANGES decision and include all pending comments

### Requirement: Manual Queue Refresh
The system SHALL provide a manual refresh trigger to re-query GitHub and re-score the queue on demand.

#### Scenario: Trigger manual refresh
- **WHEN** the user presses the refresh key
- **THEN** the system SHALL re-fetch review requests from GitHub, re-evaluate scoring heuristics, and update the displayed queue
