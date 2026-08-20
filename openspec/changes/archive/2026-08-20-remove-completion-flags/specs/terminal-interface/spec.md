## ADDED Requirements

### Requirement: CLI help does not advertise completion options
The system SHALL NOT list `--install-completion` or `--show-completion` in the `gitkeeper` CLI help options panel when help is displayed (invoked with `--help` or as a group help output), and SHALL NOT register either option for parsing on the root command.

#### Scenario: Help invoked shows no completion options
- **WHEN** a user invokes `gitkeeper --help`
- **THEN** the options panel SHALL contain `--config` and `--help` but SHALL NOT contain `--install-completion` or `--show-completion`

#### Scenario: Completion flags are rejected
- **WHEN** a user invokes `gitkeeper --install-completion` or `gitkeeper --show-completion`
- **THEN** the system SHALL respond as with any unknown option, and SHALL NOT install or display shell completion scripts