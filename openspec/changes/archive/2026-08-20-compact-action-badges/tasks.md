## 1. Badge map

- [x] 1.1 Replace `ACTION_BADGES` in `gitkeeper/ui/list_view.py:14-18` with single-character glyphs: `ME_ACTIVE: ("● ", "bold cyan")`, `WAITING_OTHERS: ("○ ", "bright_black")`, `WAITING_AUTHOR: ("◇ ", "bright_black")`.
- [x] 1.2 In `_populate_list` (list_view.py:172-208), reserve the badge-and-number width first, then allocate the freed columns to the metadata row (author priority, repository truncates last) per design decision 2.

## 2. Tests

- [x] 2.1 Update `tests/test_ui.py` assertions pinning `"awaiting you"`, `"wait: author"`, `"wait: others"` (test_pr_list_action_badges and the `test_pr_list_*_two_rows` / wide-glyph cases around lines 273, 332, 355, 454) to assert the glyphs (`●`, `○`, `◇`) in the metadata row.
- [x] 2.2 Add an assertion that each metadata row's display width stays within the render width (measuring the glyphs via `cell_len`), covering the wide-metadata and scrollable-queue cases.

## 3. Verification

- [x] 3.1 Run the UI test suite (`uv run pytest tests/test_ui.py -q`) and confirm all cases pass.
- [x] 3.2 Run `openspec validate --change compact-action-badges` and confirm the change validates.
