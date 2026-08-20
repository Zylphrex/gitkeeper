## Context

The PR queue list (`gitkeeper/ui/list_view.py`) renders each entry as a two-row `OptionList` item. The metadata row is composed in `_populate_list` (list_view.py:172-208): a textual action badge from `ACTION_BADGES` (list_view.py:14-18), the PR number, the (truncated) repository name, and the (truncated) author, all tight against a `ROW_WIDTH` of 36 columns (list_view.py:24). The current badges (`[awaiting you]`, `[wait: author]`, `[wait: others]`) each measure 15 display cells, consuming 20 of 36 columns once the `#123 ` number is appended, starving the repository name and author.

The worded action-state lines live in two other places and stay unchanged:
- `gitkeeper/ui/app.py:165` — status-bar summary.
- `gitkeeper/ui/overview_view.py:15-19` — `ACTION_STATE_LINES`, the roomy overview pane, which doubles as the legend for the glyphs.

## Goals / Non-Goals

**Goals:**
- Replace the textual badges with single-character glyphs: `●` (ME_ACTIVE), `○` (WAITING_OTHERS), `◇` (WAITING_AUTHOR).
- Reclaim the freed columns for the repository name and author, prioritizing full author rendering over more aggressive repo truncation.
- Keep the two-row layout, truncation, scrollbar-width logic, and color coding unchanged.

**Non-Goals:**
- Changing the worded overview action-state lines or status-bar summary (they remain the legend).
- Changing truncation to non-ellipsis forms.
- Color changes or any change to queue ordering/scoring.

## Decisions

### 1. Single-character glyph map
- **Decision**: `ACTION_BADGES` becomes `{ME_ACTIVE: ("● ", "bold cyan"), WAITING_OTHERS: ("○ ", "bright_black"), WAITING_AUTHOR: ("◇ ", "bright_black")}`. The trailing space is the single-column separator; no brackets.
- **Rationale**: All three glyphs are single-width display cells (verified via `rich.cells.cell_len`), saving ~9 columns per row versus today. Color still carries active-vs-not; the glyph keeps author-vs-others distinguishable without relying on color alone.

### 2. Author-priority truncation on the metadata row
- **Decision**: In `_populate_list`, compute the badge + number cost first, then favor the author: truncate the repository name to what remains after reserving a floor for the author, and only truncate the author when the repo floor is saturated.
- **Rationale**: The user's stated pain is that both repo and author are barely visible; with ~9 freed columns, the natural allocation is to render the author in full and spend the surplus on the repository, preserving the existing "truncate repo first" rule from the spec.

### 3. Tests assert glyphs, not words
- **Decision**: Update the four `tests/test_ui.py` assertions that pin `"awaiting you"` / `"wait: author"` to instead assert the glyphs appear in the metadata row, plus a width regression assertion that the metadata row never exceeds the render width.
- **Rationale**: Keeps the regression coverage the strings provided, adapted to the new representation.

## Risks / Trade-offs

- **[Risk] Glyph font coverage** — `◇` in particular may render as a fallback/tofu box in some terminal fonts. **Mitigation**: the metadata row must remain ≤ render width either way (glyph is single-width), and the colored overview legend gives the meaning; an acceptable degradation is to swap `◇` for `▲` if it renders poorly for the user.
- **[Risk] Test brittleness on glyph width** — assertions must use `cell_len` on the glyphs rather than hard-coding widths, so they hold across fonts/terminals.
