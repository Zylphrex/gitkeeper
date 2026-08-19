## 1. Row budget width fix

- [x] 1.1 Update `_effective_row_width` in `gitkeeper/ui/list_view.py` to derive the available width from `option_list.scrollable_content_region.width` (falling back to `content_region.width`, then the existing `ROW_WIDTH` guards) so the budget never exceeds the width options are rendered at
- [x] 1.2 Keep the 1-column safety margin and `MIN_ROW_WIDTH`/`ROW_WIDTH` clamps so truncated rows stop short of the wrap threshold

## 2. Scrollbar-transition handling

- [x] 2.1 Add a `watch` on `OptionList.vertical_scrollbar.visible` in `PRListView` that calls the existing re-measure/re-populate path when the scrollbar appears or disappears (covers the no-resize-event transition when the queue crosses the viewport height)
- [x] 2.2 Ensure the re-measure path preserves the currently highlighted option

## 3. Cell-aware truncation

- [x] 3.1 Make `_truncate` in `list_view.py` trim by display cells (`rich.cells.cell_len`) so the ellipsis stays within `width` columns for wide glyphs (CJK/emoji) and never exceeds the budget
- [x] 3.2 Update the metadata-budget arithmetic in `_populate_list` to allocate repo/author space by cell width instead of code-point length

## 4. Tests

- [x] 4.1 Add a scrollable-queue test (many PRs, e.g. 15+, sized so the list scrolls) asserting every entry renders as exactly two rows with `@author` on the metadata row and a single truncated title row
- [x] 4.2 Add a wide-glyph test (CJK repo name / author / title) asserting exactly two rows and no wrap, pinning the cell-aware truncation
- [x] 4.3 Keep existing tests green (`test_pr_list_long_title_ellipsized_flush_left`, `test_pr_list_option_shows_author_without_reason_chip`, `test_pr_list_rows_shrink_when_window_is_narrow`, `test_pr_list_rows_reflow_on_resize`), adjusting only if the new budget makes their fixtures rely on stale widths

## 5. Verification

- [x] 5.1 Run `uv run pytest tests/test_ui.py` (full suite if fast) and fix any regressions
- [x] 5.2 Run the linter/type checker configured for the repo (`ruff`/`mypy` if present) on changed files
- [x] 5.3 Manually render the list with a long queue (scrollbar visible) and a short queue to confirm two-row layout in both states