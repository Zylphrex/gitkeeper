## Context

`gitkeeper` is a TUI-first CLI with a single root command (no subcommands). Typer 0.27.1 auto-injects `--install-completion` and `--show-completion` into the root group (`typer/main.py:1174-1186`) unless `add_completion=False` is passed. They appear in the only help screen users see. See proposal.md - Why.

## Goals / Non-Goals

**Goals:**
- Remove the two completion options from the options panel and from command parsing.
- Minimal, low-risk change to the CLI surface.

**Non-Goals:**
- Re-adding completion via a different surface (e.g., a `completion` subcommand or docs instructions).
- Changing how completion works for users who already installed a snippet.

## Decisions

- **Disable Typer's built-in completion options via `add_completion=False`** (cli.py:47) rather than hiding them with `hidden=True` or filtering params post-hoc.
  - Rationale: `hidden` suppresses help display but leaves the options registered, so `gitkeeper --install-completion` would still execute. `add_completion=False` removes both options entirely, matching the spec's "SHALL NOT register either option for parsing."
  - Alternatives considered: no-op callbacks that print an error (keeps parse noise), overridden `format_help` that strips rows (fragile against Typer internals).

## Risks / Trade-offs

- [Users who relied on the flags to install completion lose the CLI path] → No longer documented or advertised; users with an installed snippet are unaffected. This is the accepted cost, captured in the proposal as BREAKING.
- [Typer upgrade could change how completion injection toggles] → `add_completion` is a stable documented constructor argument; `test_cli.py` regression guards the help output contract.