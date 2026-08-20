## MODIFIED Requirements

### Requirement: Global Motion Keys
The system SHALL provide Vim-style motion keys that work consistently across all scrollable and list-based widgets, with arrow keys `up`/`down` behaving identically to `j`/`k`.

#### Scenario: Navigate up and down with j/k
- **WHEN** the user is focused on any scrollable or list widget (PR list, file list, diff viewer)
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