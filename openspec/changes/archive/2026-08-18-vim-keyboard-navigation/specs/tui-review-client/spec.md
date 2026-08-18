## MODIFIED Requirements

### Requirement: Interactive PR Queue Navigation
The system SHALL provide a full-screen interactive interface listing actionable pull requests ranked by relevance score in a singular continuous list with keyboard and mouse navigation.

#### Scenario: Navigate ranked pull requests
- **WHEN** the TUI application loads
- **THEN** the system SHALL display the complete ranked list of actionable pull requests in the left panel sorted descending by relevance score with relevance scores, repository names, and authors
- **AND** the user SHALL be able to select and highlight different pull requests using Vim-style navigation keys (`j`/`k` for up/down, `gg`/`G` for top/bottom, `Ctrl+d`/`Ctrl+u` for paging) or arrow keys or mouse selection

#### Scenario: Display selected PR overview and rationale
- **WHEN** a pull request is selected or clicked in the queue list
- **THEN** the system SHALL display the PR metadata, full description, and detailed scoring rationale breakdown in the right overview panel
- **AND** the system SHALL synchronize the diff viewer with the newly selected pull request

### Requirement: In-TUI Diff Viewer
The system SHALL provide an interactive diff viewer allowing users to inspect file changes and patches for the selected pull request directly within the terminal interface.

#### Scenario: View file diffs for a pull request
- **WHEN** the user switches to the diff view for a selected pull request
- **THEN** the system SHALL display the list of modified files and the syntax-highlighted unified diff of the selected file

#### Scenario: Navigate through diff hunks and files
- **WHEN** inspecting a diff
- **THEN** the user SHALL be able to navigate between files and scroll through diff lines with Vim-style navigation keys (`j`/`k` for up/down lines, `gg`/`G` for top/bottom, `Ctrl+d`/`Ctrl+u` for paging) and arrow keys
- **AND** the user SHALL be able to switch focus between the file list and the diff viewer using `h`/`l`