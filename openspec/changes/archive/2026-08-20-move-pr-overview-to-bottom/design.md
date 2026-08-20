## Context

See proposal.md for motivation. Current structure (`gitkeeper/ui/app.py:126-135`): a `Horizontal(id="main-container")` holds three siblings — `PRListView` (fixed 42 cols), `PRDiffView` inside `Vertical(id="right-tabs")` (1fr), and `PROverviewView` (fixed 44 cols, border-left). `PROverviewView` (`overview_view.py`) is itself a vertical stack of three content boxes: `#pr-meta-box`, `#pr-score-box`, and `#pr-body-scroll` (a `VerticalScroll` wrapping the markdown). PR-list row width in `list_view.py` clamps against a right-hand overview column via `_effective_row_width`.

The description is currently a `VerticalScroll` (scrollable); the new behavior makes it a non-scrollable fixed-height preview that is not a focus target, and the overview moves from the right column to a full-width bottom row.

## Goals / Non-Goals

**Goals:**
- Overview occupies a full-width bottom row of fixed height, split into left (meta + score) and right (description preview) columns.
- Diff pane frees the ~44 columns the overview consumed, spanning the full top row width.
- No new keyboard focus zones; the description is read-only.
- Reuse the existing `update_pr()`/markdown debounce machinery.

**Non-Goals:**
- Making the description scrollable or a search target.
- Making the bottom-row height user-configurable (addressed only as a constant the CSS could later parametrize).
- Changing any metadata content, viewer-status derivation, or markdown rendering behavior.

## Decisions

### D1: Reuse `PROverviewView` as the bottom-row widget (no split widget)
The widget already renders meta + score + body and owns all wiring (`update_pr()`, markdown worker, debounce). Restructure its `compose()` to a `Horizontal` holding the stacked meta/score boxes on the left and the description as the right child, rather than splitting it into two widgets. This keeps a single `update_pr()` call site and avoids re-plumbing `_refresh_overview()` / worker lifecycle.

Alternative considered: a separate `PRDescriptionView`. More isolation, but duplicates markdown plumbing and the debounce/worker lifecycle for no functional gain.

### D2. Responsive fixed bottom height via CSS
Mount the overview inside a new `Horizontal(id="bottom-row")` in `app.py`'s `compose()`. Size it with `height: 40%; max-height: 16` rather than a hard `1fr` or a fixed integer: on normal terminals the row reaches ~16 rows, while on very short terminals it degrades to ~40% of the window so the PR list keeps usable height. Rationale: the description is a preview, not a reading span; the capped height keeps the top diff area's height stable while staying usable on short screens. The numbers are tokens that a future config value could govern.

### D3. Description loses the `VerticalScroll` shell
Given the non-scrollable requirement, render the description as a `Markdown` directly (or a plain container), removing vertical scrolling entirely. This removes the widget from j/k scroll dispatch — `_dispatch_option_or_scroll` in `app.py` already no-ops for unfocusable widgets, so no focus-graph change is needed. Keep the debounced exclusive-worker markdown update logic.

### D4. PR-list row budget no longer clamps against the overview column
`_effective_row_width` in `list_view.py` caps against a right-hand pane (`screen_width - 4`). With the overview gone from the right, the list no longer needs that carve-out; the row budget should measure the actual pane width only. Diff pane similarly expands (its `1fr` now spans the freed columns).

### D5. Bottom-left meta column wrapping
Meta rows already wrap by design (they're `Label` text with `width: 1fr` and the meta box uses `height: auto`). With a fixed-height bottom row, the left column must be allowed to grow up to that fixed height; any meta content beyond it is clipped by the row's fixed height. The score box and meta box keep `height: auto` so the description inherits the leftover width.

## Risks / Trade-offs

- [Responsive bottom height] → On a very short terminal the bottom row degrades to ~40% of the window, which reduces the available description preview height to a few rows. Mitigation: the diff pane and PR list keep usable height (the reason for shrinking); the description preview shallowly shows the start of the body, and the full body remains one `o` keypress away in the browser.
- [Description is not scrollable] → Long PR bodies become unreadable in the TUI; users can open in browser (`o`). Mitigation: keep the description rendering the truncated-by-clip portion; no functional loss beyond current wide-pane capability.
- [Row budget removal changes] → PR list truncation previously assumed a specific maximum width; removing the overview clamp means rows may now be wider or keep current computed widths depending on terminal size. Mitigation: rely on the same `_effective_row_width` live measurement; verify row widths on narrow terminals via the existing test scenarios.

## Migration Plan

This is a TUI layout change with no data or persistence. Rollback is a revert of the layout diff plus the spec/design tasks; the app remains internally consistent since focus zones and data flow are unchanged.

## Open Questions

None — behavioral scope (scroll, focus, height budget) was resolved during exploration: full-width bottom row, fixed height, no scroll/focus additions, title stays in the bottom meta column.