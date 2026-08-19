## 1. List widget changes

- [x] 1.1 Add a `ROW_WIDTH = 40` constant and an ellipsis truncation helper (`_truncate(text, width)`) to `gitkeeper/ui/list_view.py`, with a comment deriving the budget from the 42-col panel (mirroring the `filestree.py` convention).
- [x] 1.2 Rewrite `_populate_list` so line 1 renders `[tier] #number <short repo>  @author` with the author styled dim and the repo ellipsis-truncated when the line would exceed `ROW_WIDTH`.
- [x] 1.3 Move the title to its own flush-left line, truncated to `ROW_WIDTH` with a trailing `…`; remove the `reason` lookup, the `(reason)` chip, and the `[:22]` slicing.

## 2. Tests

- [x] 2.1 Add a test asserting a populated queue option contains the author (`@alice`) on the first line and no longer contains any `(reason)` chip fragment.
- [x] 2.2 Add a test asserting a long title (`LONG_PR_TITLE`) is ellipsised (`…`) and that its second line is flush-left (no leading spaces) and unwrapped.
- [x] 2.3 Add a test asserting a short title renders untruncated with no ellipsis.

## 3. Verification

- [x] 3.1 Run `uv run pytest tests/test_ui.py -q` and confirm the new and existing list tests pass.
- [x] 3.2 Run the full suite `uv run pytest -q` and confirm no regressions.
- [x] 3.3 Manually render the queue left panel in a headless Textual run at 42 columns and confirm rows are exactly two lines with no wrapping.

## 4. Width and resize hardening

- [x] 4.1 Clamp the effective row width to the actual pane/screen width (with a `MIN_ROW_WIDTH` floor) so narrow windows degrade instead of wrapping rows.
- [x] 4.2 Re-measure on window resize via an app-level `on_resize` hook plus the widget's `on_resize`, preserving the highlighted selection.
- [x] 4.3 Add regression tests for narrow-window launch and live resize reflow.