## ADDED Requirements

### Requirement: Hide Whitespace in Diff View

The system SHALL provide a review-tunable diff mode that hides whitespace-only differences by comparing changed lines with whitespace ignored (the same comparison `git diff -w` uses), so that a line pair differing only in whitespace SHALL be rendered as unchanged context instead of an added/deleted change pair, and a hunk whose differences collapse entirely to whitespace SHALL be dropped from the displayed diff. The mode SHALL NOT alter any change lines that differ beyond whitespace, and the mode SHALL be session-scoped (not persisted to config).

The reviewer SHALL be able to toggle the mode on and off while reviewing, and the system SHALL show a clear active-mode indicator within the diff view so a reviewer is never silently looking at a filtered diff.

#### Scenario: Toggle whitespace hiding with the w key

- **WHEN** the reviewer presses the toggle key (`w`) while the diff view is loaded
- **THEN** the system SHALL invert the whitespace-hiding mode
- **AND** the system SHALL re-render the currently displayed pull request's diff from the cached diff text without refetching from GitHub

#### Scenario: A line that differs only in whitespace is hidden

- **WHEN** whitespace-hiding mode is active AND a deleted line and an added line in the same hunk are equal once all whitespace is removed
- **THEN** the system SHALL render that content as a single context line (no addition or deletion prefix) rather than a `-`/`+` change pair
- **AND** the context line SHALL carry the correct new-file and old-file line numbers

#### Scenario: A hunk that collapses is dropped

- **WHEN** whitespace-hiding mode is active AND every change line in a hunk belongs to a whitespace-only pair
- **THEN** the system SHALL drop that hunk from the rendered diff

#### Scenario: Non-whitespace changes are unaffected

- **WHEN** whitespace-hiding mode is active AND a hunk contains change lines that differ beyond whitespace
- **THEN** the system SHALL keep those change pairs rendered exactly as they would be in the default mode, and any whitespace-only pairs within the same hunk SHALL still be collapsed to context

#### Scenario: Mode defaults to off per session

- **WHEN** the TUI application starts
- **THEN** the whitespace-hiding mode SHALL be disabled
- **AND** the diff SHALL render with all whitespace-only changes visible until the reviewer toggles the mode

#### Scenario: Active mode is indicated

- **WHEN** whitespace-hiding mode is active
- **THEN** the diff view SHALL display a visible indicator (e.g. a header label or footer key hint) that the mode is on
- **AND** the indicator SHALL disappear or revert when the mode is toggled off