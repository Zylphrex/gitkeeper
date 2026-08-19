## MODIFIED Requirements

### Requirement: Inline and Top-Level Commenting
The system SHALL allow users to author inline review comments on specific diff lines as well as top-level review comments from within the interface.

The system SHALL reliably route the inline comment action to the inline comment input dialog for the currently selected diff line, so that the dialog SHALL open whenever the user triggers the comment action while a diff line is selected, regardless of message dispatch naming conventions in the UI framework.

#### Scenario: Add inline comment on a diff line
- **WHEN** the user selects a specific line in the diff view and triggers the comment action
- **THEN** the system SHALL open an input dialog allowing the user to enter markdown feedback
- **AND** the dialog SHALL open immediately for the selected file and line without requiring any extra step
- **AND** attach the pending comment to that file and line number
- **AND** make the pending comment available for inclusion in a subsequent review submission
