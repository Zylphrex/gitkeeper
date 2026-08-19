## MODIFIED Requirements

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