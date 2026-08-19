## Context

The PR queue list renders each entry as a two-line `Text` prompt in a textual `OptionList`. `PRListView._effective_row_width` computes a row budget from `option_list.content_region.width`, but `OptionList` actually renders option lines at `scrollable_content_region.width` (which is the same until a vertical scrollbar appears, then 2 columns narrower). When the queue outgrows the pane the budget (36) exceeds the render width (35) and every row that fills its budget soft-wraps. See proposal.md - Why.

Full mechanism and rendered repro: the option `Text` keeps two logical lines, but `OptionList` re-wraps the first line inside the widget, so each affected entry renders 3-4 rows rather than 2.

## Goals / Non-Goals

**Goals:**
- Every queue entry renders as exactly two rows, whether or not the list is scrollable.
- The budget the TUI truncates against is always ≤ the width options are actually rendered at.
- Keep the existing two-row ASCII invariants covered by `tests/test_ui.py` passing unchanged.

**Non-Goals:**
- Changing the pane width (still 42), the two-row visual design, or any queue/selection behavior.
- Re-layout of the file tree pane or overview panel (same bug class exists in `filestree.py` but is not reported; leaving it out of this change).

## Decisions

### D1: Budget from the scrollable content width, not the content width
`_effective_row_width` will compute the available width as `option_list.scrollable_content_region.width - option_list._get_left_gutter_width()` (the exact width `_get_option_render`/`_update_lines` wrap lines at in the installed textual 8.x), falling back to `content_region` when it is not available. This makes the TUI's truncation limit match OptionList's wrap width by construction.

**Alternatives considered:**
- Keeping `content_region` and subtracting a fixed `2` for the scrollbar. Rejected: couples us to a hard-coded scrollbar thickness and still breaks if textual's gutter handling changes.

### D2: Assume the scrollbar may appear; reserve nothing but rely on D1's width
Because `scrollable_content_region` already excludes the scrollbar when visible, D1 inherently handles the scrollable case. The remaining risk is *transition*: the scrollbar appears/disappears (queue crosses the viewport height) without a resize event, leaving the memoized budget stale. Textual emits no resize when the scrollbar toggles.

**Resolution:** recompute the budget (and re-populate the option list) whenever `OptionList.vertical_scrollbar.visible` changes, in addition to the existing `on_resize`/`refresh_row_width` paths. `visible` is a tracked reactive in textual, so a `@watch` on it is the natural hook.

**Alternatives considered:**
- Always subtracting the scrollbar width even when hidden. Rejected: wastes width on short queues and doesn't cover other gutter sources.
- Re-measuring on every data refresh only. Rejected: `set_pull_requests` already re-populates, but the bug triggers *within* a fixed queue when the scrollbar state changes (e.g., filtering), so a reactive hook is needed for correctness.

### D3: Make truncation cell-aware (`rich.cells.cell_len`)
`_truncate` currently trims by code-point `len()`, so wide glyphs (CJK/emoji) still overflow the render width and wrap — violating the no-wrap invariant under non-ASCII input. Since the same two-line layout is at stake and the change is contained to `_truncate` (and the budget arithmetic in `_populate_list`), use cell width so truncation limits are honored in rendered columns, not characters.

**Alternatives considered:**
- Leaving truncation code-point-based. Rejected: the spec forbids wrapping, and this is the second independent way a row exceeds its render width.

## Risks / Trade-offs

- [Coupling to `scrollable_content_region` semantics] → Grounded in the installed textual version (8.2.8); existing tests already depend on OptionList internals (`content_region`), and the budget formula is covered by rendering tests that paint rows.
- [Stale memoized `_row_width` if another gutter source appears (e.g. scrollbar-replacement)] → The width is re-derived from `scrollable_content_region` on every re-populate; the `visible` watch makes the transition path trigger a re-populate.
- [Cell-aware truncation marginally changes how long wide-glyph rows truncate] → Rows visually still end with `…` and fit the pane; only the cut point changes.
- [Scope: `filestree.py` mirrors the same `len()` pattern] → Accepted as a non-goal; noted in the proposal so it can be picked up separately.

## Migration Plan

No data or config migration. Pure UI fix; rollback is a revert of the `list_view.py`/`test_ui.py` changes.

## Open Questions

None.