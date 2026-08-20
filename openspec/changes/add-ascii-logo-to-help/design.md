## Context

`gitkeeper/cli.py` builds the CLI with `typer.Typer(help=...)` and a single callback. Typer (0.27.x) renders `--help` through `typer.main.TyperGroup.format_help`, which — when Rich is available — delegates to `typer.rich_utils.rich_format_help()`. That function prints the usage line, help text, option panels, and epilog directly to a Rich `Console`; the click `HelpFormatter` never produces the visible output.

Key constraint: Typer's `_get_help_text` collapses single newlines in the `help=` prose before rendering, so multi-line ASCII art placed in `help=` gets flattened into one line. An `epilog=` is also linebreak-collapsed. Embedding a banner in prose strings is therefore not viable.

## Goals / Non-Goals

**Goals:**

- Place an ASCII logo banner above the usage line in `gitkeeper --help` output.
- Keep Typer's existing Rich panels (options, commands) rendering unchanged.
- Keep the logo short enough to avoid wrapping in common terminal widths.

**Non-Goals:**

- No splash or watermark in the interactive TUI — purely the CLI help screen.
- No config flag to toggle the logo on/off.
- No new runtime dependencies (e.g., `pyfiglet`).

## Decisions

### D1: Override `format_help` via a custom `TyperGroup` subclass

Implement `gitkeeper.cli.BrandedTyperGroup` extending `typer.main.TyperGroup`, wired into the app with `typer.Typer(..., cls=BrandedTyperGroup)`. Override `format_help` so that, on the Rich code path, it prints the banner first, then calls `typer.rich_utils.rich_format_help(obj=self, ctx=ctx, markup_mode=self.rich_markup_mode)`.

This is the only injection point that runs for `--help` at group level without changing Typer's panel logic.

**Alternatives considered:**

- `help=` / `epilog=` strings → rejected: single newlines are collapsed (`_get_help_text` + `_fix_linebreaks`), so a multi-line banner would be mangled.
- A callback that intercepts `--help` → would need to parse args manually; loses Typer's own help panel behavior and error handling.

### D2: Render the banner as an ANSI-styled `Text`, not markup

The logo uses the ANSI-colored block-graphics font supplied by the user. Because `[` and `_` interact with both Rich markup parsing and Typer's highlighter, the banner is stored as ANSI escape sequences and printed via `Text.from_ansi(BANNER)` — the parsed `Text` skips markup parsing and default highlighting while preserving the intended foreground colors.

### D3: Terminal-transparent background banner

The source font encodes solid black (`;40m`) and white (`;47m`) background stripes. Those background codes are stripped when building `BANNER`, so only foreground colors remain and the block glyphs render over the terminal's own background instead of a fixed dark/light box. The shade characters (`░▒▓`) fall back to the terminal default where color is unsupported, keeping the logo legible in `CliRunner` captured output.

The exact glyphs are cosmetic; the implementer may iterate on the final banner during apply. The constraint (safe charset, short lines, no wrapping) is binding.

## Risks / Trade-offs

- [Typer may change internal rendering APIs] → Mitigation: pin to typer>=0.9 (already in `pyproject.toml`), keep the override minimal, and add a test asserting the banner appears verbatim so regressions surface.
- [Banner tagged inline in `help` output encodes ANSI codes in captured tests] → Mitigation: tests assert on a plain substring of the banner constant, not whole-line equality.
- [Narrow-terminal wrapping of the banner could look broken] → Mitigation: short banner lines + Rich console `overflow="fold"` on the banner print's own Renderable so the options panel layout is never affected.
- [Overriding `format_help` may be bypassed when click takes the non-Rich path (e.g., `-h` via click)] → tradeoff: acceptable because the Rich path is what runs under normal installs. If click-only fallback is wanted later, the override can delegate to the superclass before printing the banner there.

## Migration Plan

- Deploy as part of the next release; no data migration.
- Rollback: revert the `cls=` + `format_help` override; behavior returns to stock Typer help.

## Open Questions

- None blocking. The final banner line-art (whether it spells `GITKEEPER`, uses a key/shield shape, etc.) is cosmetic and safe to decide during implementation without changing spec or task breakdown.