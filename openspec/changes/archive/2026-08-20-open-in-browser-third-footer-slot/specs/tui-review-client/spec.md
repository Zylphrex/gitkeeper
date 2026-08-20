## ADDED Requirements

### Requirement: Open-in-Browser Hot Key Display Order
The system SHALL render the open-in-browser key (`o`) as the third item in the footer hot-key list in every focus zone and modal-free state, preceded only by the quit key (`q`) and the refresh key (`r`), regardless of which review action keys (`c`, `s`, `w`) are also displayed.

#### Scenario: Open key is third while review action keys are hidden
- **WHEN** focus is in the PR list zone, or no widget is focused (so the review action keys `c`, `s`, `w` are hidden)
- **THEN** the footer SHALL display the hot keys in the order `q`, `r`, `o`, with `o` as the third item
- **AND** the footer SHALL NOT display any review action key

#### Scenario: Open key is third while review action keys are shown
- **WHEN** focus is in the changed-files list or the diff viewer (so the review action keys `c`, `s`, `w` are shown)
- **THEN** the footer SHALL display the hot keys in the order `q`, `r`, `o`, `c`, `s`, `w`, with `o` as the third item
- **AND** `o` SHALL NOT be displaced by the review action keys

#### Scenario: Open key is third when no diff is loaded
- **WHEN** focus is in the changed-files list or the diff viewer but the diff is not yet loaded or is in an error state
- **THEN** `o` SHALL remain the third displayed footer item