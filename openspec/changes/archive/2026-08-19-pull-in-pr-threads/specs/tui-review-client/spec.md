## MODIFIED Requirements

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
- **AND** threads whose target line cannot be matched to a rendered diff line SHALL NOT be displayed

#### Scenario: Existing threads and pending comment on the same line
- **WHEN** a diff line has both existing review threads and a pending comment authored by the reviewer
- **THEN** the system SHALL display the existing threads and the pending comment together on that line
- **AND** the pending comment SHALL remain visually distinct from the existing threads

#### Scenario: Thread fetch fails while viewing a diff
- **WHEN** fetching existing review threads for a pull request fails
- **THEN** the diff SHALL still be displayed and navigable
- **AND** the system SHALL report the thread fetch failure in the status display