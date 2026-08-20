## 1. Disable Completion Options

- [x] 1.1 Pass `add_completion=False` to the `typer.Typer(...)` constructor in `gitkeeper/cli.py` so Typer no longer injects `--install-completion` / `--show-completion` into the root group

## 2. Regression Coverage

- [x] 2.1 Add a test in `tests/test_cli.py` invoking `gitkeeper --help` and asserting the options panel does NOT contain `--install-completion` or `--show-completion` while still containing `--config` and `--help`
- [x] 2.2 Run the test suite (`pytest`) and confirm existing CLI tests (`test_cli_missing_token`, `test_cli_launches_tui`, `test_cli_help_shows_banner`, `test_cli_help_with_config_does_not_launch_tui`) still pass