## Purpose

Provides a consistent Vim-inspired keyboard navigation system across all TUI widgets, enabling power users to navigate, focus, and search without leaving the home row.

## Requirements

### Requirement: Global Motion Keys
The system SHALL provide Vim-style motion keys that work consistently across all scrollable and list-based widgets.

#### Scenario: Navigate up and down with j/k
- **WHEN** the user is focused on any scrollable or list widget (PR list, overview body, file list, diff viewer)
- **THEN** pressing `j` SHALL move the cursor or scroll one position down
- **AND** pressing `k` SHALL move the cursor or scroll one position up

#### Scenario: Jump to top and bottom with gg and G
- **WHEN** the user is focused on any scrollable or list widget
- **THEN** pressing `g` twice (`gg`) SHALL jump to the first item or top of content
- **AND** pressing `G` SHALL jump to the last item or bottom of content

#### Scenario: Page up and down with Ctrl+u and Ctrl+d
- **WHEN** the user is focused on any scrollable or list widget
- **THEN** pressing `Ctrl+u` SHALL scroll up by half a page
- **AND** pressing `Ctrl+d` SHALL scroll down by half a page

### Requirement: Focus Movement
The system SHALL allow moving focus between UI panes using directional keys.

#### Scenario: Move focus with h and l
- **WHEN** the user presses `l`
- **THEN** focus SHALL move to the next pane to the right according to the focus graph
- **WHEN** the user presses `h`
- **THEN** focus SHALL move to the next pane to the left according to the focus graph
- **AND** Tab SHALL continue to work as an alternative focus cycle through all panes

#### Scenario: Focus graph boundaries
- **WHEN** focus is at the leftmost pane and the user presses `h`
- **THEN** focus SHALL remain unchanged (no-op)
- **WHEN** focus is at the rightmost pane and the user presses `l`
- **THEN** focus SHALL remain unchanged (no-op)

### Requirement: Search and Filter
The system SHALL provide a search mode activated by `/` that filters or highlights content in the focused widget.

#### Scenario: Activate search with forward slash
- **WHEN** the user presses `/`
- **THEN** the system SHALL enter search mode, displaying a search prompt
- **WHEN** the user types a query and presses Enter
- **THEN** the system SHALL highlight or filter matching items in the focused widget

#### Scenario: Navigate search results
- **WHEN** search results are active
- **THEN** pressing `n` SHALL jump to the next match
- **AND** pressing `N` SHALL jump to the previous match

#### Scenario: Dismiss search
- **WHEN** the user presses Escape while in search mode
- **THEN** the system SHALL clear the search prompt and exit search mode

### Requirement: Escape as Universal Cancel
The system SHALL use Escape as a consistent cancel/close/back action across all contexts.

#### Scenario: Escape closes modals
- **WHEN** a modal is open (e.g., InlineCommentModal, SubmitReviewModal)
- **THEN** pressing Escape SHALL close the modal without accepting changes

#### Scenario: Escape clears search
- **WHEN** search mode is active
- **THEN** pressing Escape SHALL clear the search and exit search mode

#### Scenario: Escape has no effect in idle state
- **WHEN** no modal or search is active and the user presses Escape
- **THEN** the system SHALL do nothing (no-op)