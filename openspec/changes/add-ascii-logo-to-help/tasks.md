## 1. Banner constant

- [x] 1.1 Define the `BANNER` constant in `gitkeeper/cli.py` using the provided ANSI-colored block-graphics font, with its background-color codes (`;40m`, `;47m`) stripped so the glyphs render on the terminal's own background
- [x] 1.2 Verify the banner renders cleanly at 80-column width with no wrapped or corrupted lines

## 2. Custom group class

- [x] 2.1 Add `BrandedTyperGroup(TyperGroup)` in `gitkeeper/cli.py` overriding `format_help` to print the banner via a `Text.from_ansi` renderable (preserving ANSI colors while skipping Rich markup parsing) before delegating to `typer.rich_utils.rich_format_help`
- [x] 2.2 Pass `cls=BrandedTyperGroup` into `typer.Typer(...)` in `gitkeeper/cli.py`
- [x] 2.3 Confirm `gitkeeper --help` shows the banner above the usage line and the options/commands panels are unchanged

## 3. Tests

- [x] 3.1 Add a test in `tests/test_cli.py` asserting `gitkeeper --help` exits 0 and the output contains a plain substring from the logo constant
- [x] 3.2 Add a test asserting help with `--config` still includes the banner and does not invoke the TUI
- [x] 3.3 Run the full test suite and confirm existing CLI/TUI tests still pass