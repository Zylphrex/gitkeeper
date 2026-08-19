## MODIFIED Requirements

### Requirement: Inline and Top-Level Commenting
The system SHALL allow users to author inline review comments on specific diff lines as well as top-level review comments from within the interface.

The system SHALL reliably route the inline comment action to the inline comment input dialog for the currently selected diff line, so that the dialog SHALL open whenever the user triggers the comment action while a diff line is selected, regardless of message dispatch naming conventions in the UI framework.

The system SHALL preserve the reviewer's position in the diff view when an inline comment is saved: the selected file, highlighted line, scroll position, and focus SHALL remain as they were when the comment action was triggered.

#### Scenario: Add inline comment on a diff line
- **WHEN** the user selects a specific line in the diff view and triggers the comment action
- **THEN** the system SHALL open an input dialog allowing the user to enter markdown feedback
- **AND** the dialog SHALL open immediately for the selected file and line without requiring any extra step
- **AND** attach the pending comment to that file and line number
- **AND** make the pending comment available for inclusion in a subsequent review submission

#### Scenario: Saving a comment preserves the diff position
- **WHEN** the user saves an inline comment on a line in a diff file
- **THEN** the system SHALL keep the commented file selected in the file tree
- **AND** the system SHALL keep the commented line highlighted in the diff view
- **AND** the system SHALL keep the current scroll position and focus in the diff pane
- **AND** the system SHALL display the pending comment on the commented line immediately after saving

#### Scenario: Cancelling a comment preserves the diff position
- **WHEN** the user cancels the inline comment dialog
- **THEN** the system SHALL return to the diff viewer with the file selection, line highlight, scroll position, and focus unchanged
- **AND** the system SHALL NOT attach any comment