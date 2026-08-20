## ADDED Requirements

### Requirement: CLI help shows ASCII logo banner
The system SHALL render an ASCII logo banner above the usage line when the `gitkeeper` CLI help is displayed (invoked with `--help` or as a group help output). The banner SHALL render using terminal-width-aware formatting so it does not overflow narrow terminals.

#### Scenario: Help invoked with no token configured
- **WHEN** a user invokes `gitkeeper --help`
- **THEN** the output SHALL begin with the ASCII logo banner, followed by the usage line and options panel, and errors related to token configuration SHALL NOT be raised

#### Scenario: Help rendered on a narrow terminal
- **WHEN** a user invokes `gitkeeper --help` on a terminal narrower than the banner text
- **THEN** the system SHALL render the banner without emitting a wrapped or corrupted layout that breaks the options panel alignment