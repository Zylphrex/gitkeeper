## MODIFIED Requirements

### Requirement: Global Motion Keys
The system SHALL provide Vim-style motion keys that work consistently across all scrollable and list-based widgets, with arrow keys `up`/`down` behaving identically to `j`/`k`.

#### Scenario: Navigate up and down with j/k
- **WHEN** the user is focused on any scrollable or list widget (PR list, overview body, file list, diff viewer)
- **THEN** pressing `j` SHALL move the cursor or scroll one position down
- **AND** pressing `k` SHALL move the cursor or scroll one position up

#### Scenario: Navigate up and down with arrow keys
- **WHEN** the user is focused on any scrollable or list widget
- **THEN** pressing `down` SHALL move the cursor or scroll one position down
- **AND** pressing `up` SHALL move the cursor or scroll one position up

#### Scenario: Jump to top and bottom with gg and G
- **WHEN** the user is focused on any scrollable or list widget
- **THEN** pressing `g` twice (`gg`) SHALL jump to the first item or top of content
- **AND** pressing `G` SHALL jump to the last item or bottom of content

#### Scenario: Page up and down with Ctrl+u and Ctrl+d
- **WHEN** the user is focused on any scrollable or list widget
- **THEN** pressing `Ctrl+u` SHALL scroll up by half a page
- **AND** pressing `Ctrl+d` SHALL scroll down by half a page

#### Scenario: Widget-native arrow handling takes priority
- **WHEN** the focused widget binds arrow keys natively (e.g. text input cursor movement)
- **THEN** the arrow key SHALL perform the widget's native behavior and SHALL NOT trigger app-level navigation

### Requirement: Focus Movement
The system SHALL allow moving focus between UI panes using directional keys, with arrow keys `left`/`right` behaving identically to `h`/`l`.

#### Scenario: Move focus with h and l
- **WHEN** the user presses `l`
- **THEN** focus SHALL move to the next pane to the right according to the focus graph
- **WHEN** the user presses `h`
- **THEN** focus SHALL move to the next pane to the left according to the focus graph
- **AND** Tab SHALL continue to work as an alternative focus cycle through all panes

#### Scenario: Move focus with left and right arrow keys
- **WHEN** the user presses `right`
- **THEN** focus SHALL move to the next pane to the right according to the focus graph
- **WHEN** the user presses `left`
- **THEN** focus SHALL move to the next pane to the left according to the focus graph

#### Scenario: Focus graph boundaries
- **WHEN** focus is at the leftmost pane and the user presses `h` or `left`
- **THEN** focus SHALL remain unchanged (no-op)
- **WHEN** focus is at the rightmost pane and the user presses `l` or `right`
- **THEN** focus SHALL remain unchanged (no-op)