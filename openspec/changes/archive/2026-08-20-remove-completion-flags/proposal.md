## Why

The `gitkeeper --help` options panel advertises `--install-completion` and `--show-completion`, but the CLI is a TUI-first tool with no subcommands and these flags do nothing but exit. They add foothold noise to the one screen users actually see, and their interface is only meaningful on a subcommand-oriented CLI.

## What Changes

- **BREAKING**: Remove the `--install-completion` and `--show-completion` options from the root Typer group so they no longer appear in the options panel.
- Shell completion for `gitkeeper` is no longer advertised or installable through the CLI itself. Completion snippets already installed continue to work.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `terminal-interface`: the CLI help options panel SHALL NOT list shell-completion options (`--install-completion`, `--show-completion`)

## Impact

- `gitkeeper/cli.py`: pass `add_completion=False` to the `typer.Typer(...)` constructor (cli.py:47).
- `tests/test_cli.py`: add a regression assertion that the completion options are absent from `--help` output.
- No new dependencies; Typer 0.27 already supports `add_completion=False`.