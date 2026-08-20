## Why

The `gitkeeper --help` output is currently a bare, unstyled usage page: the tagline wraps unassisted and there is no brand presence. A distinctive ASCII logo gives the CLI instant recognizability, signals polish, and matches the identity of the interactive TUI.

## What Changes

- Render an ASCII logo banner at the top of the `gitkeeper --help` output, above the usage line.
- Use a custom Typer group class so help rendering stays Rich-based and terminal-width aware.
- Keep the existing tagline and options panels unchanged.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `terminal-interface`: the CLI help screen SHALL display the ASCII logo banner when `gitkeeper --help` is invoked

## Impact

- `gitkeeper/cli.py`: introduce the custom Typer group class and wire it into the `typer.Typer(...)` app.
- `tests/test_cli.py`: coverage for the logo appearing in help output.
- No runtime dependencies added — Rich is already a dependency.