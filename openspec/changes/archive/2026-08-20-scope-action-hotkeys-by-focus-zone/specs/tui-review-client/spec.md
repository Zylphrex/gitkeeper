## ADDED Requirements

### Requirement: Zone-Scoped Review Action Keys
The system SHALL restrict the review action keys `c` (inline comment), `s` (submit review), and `w` (hide whitespace) to the right-hand diff focus zone: these keys SHALL be available (bound and displayed) only while focus is in the changed-files list or the diff viewer, and SHALL be hidden from the footer and inert whenever focus is anywhere else (including the PR list zone, no widget focused, or a modal dialog open). The keys `q`, `r`, and `o` SHALL remain available in every zone. Scoping SHALL be based on the focus zone alone and SHALL NOT depend on whether a diff is currently loaded.

#### Scenario: Diff zone focused shows all review actions
- **WHEN** focus is in the changed-files list or the diff viewer
- **THEN** the footer SHALL display the review action keys `c`, `s`, `w` alongside the global keys `q`, `r`, `o`
- **AND** pressing `c`, `s`, or `w` SHALL trigger the corresponding review action

#### Scenario: PR list zone hides review actions
- **WHEN** focus is in the PR list zone, or no widget is focused
- **THEN** the footer SHALL NOT display the review action keys `c`, `s`, `w`
- **AND** pressing `c`, `s`, or `w` SHALL NOT trigger any review action

#### Scenario: Global keys remain available in both zones
- **WHEN** focus is in the PR list zone or in the diff zone
- **THEN** `q`, `r`, and `o` SHALL remain available in both zones

#### Scenario: Review actions hidden while a modal is open
- **WHEN** a dialog modal (e.g. the inline comment modal or the submit-review modal) is open
- **THEN** the review action keys `c`, `s`, `w` SHALL NOT be displayed in the footer
- **AND** pressing `c`, `s`, or `w` SHALL NOT trigger any review action

#### Scenario: Diff pane scoping does not depend on loaded state
- **WHEN** focus is in the changed-files list or the diff viewer but the diff is not yet loaded or is in an error state
- **THEN** the review action keys `c`, `s`, `w` SHALL remain displayed in the footer
- **AND** pressing them SHALL behave according to the existing empty-state guards (e.g. reporting "No PR diff loaded.") rather than being unavailable