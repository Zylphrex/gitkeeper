## 1. Reorder the Open-in-Browser Binding

- [x] 1.1 Move `Binding("o", "open_browser", "Open in Browser")` in `GitkeeperApp.BINDINGS` (`gitkeeper/ui/app.py`) to the third slot, immediately after the `refresh` binding and before `comment_action`
- [x] 1.2 Confirm the moved binding keeps its existing key (`o`), action (`open_browser`), description (`Open in Browser`), and default `show` state unchanged
- [x] 1.3 Confirm no other binding's key, position, or description changed

## 2. Footer Ordering Tests

- [x] 2.1 Add a test asserting that with focus in the PR-list zone (`#pr-option-list`), the visible footer bindings (those with `show` truthy in `screen.active_bindings`, filtered by `binding.show`) appear in the exact order `q`, `r`, `o`
- [x] 2.2 Add a test asserting that with focus in `#diff-options`, the visible footer bindings appear in the exact order `q`, `r`, `o`, `c`, `s`, `w`
- [x] 2.3 Add a test asserting the same exact order `q`, `r`, `o`, `c`, `s`, `w` with focus in `#file-option-list`
- [x] 2.4 Add a helper in `tests/test_ui.py` (module-level) that extracts visible hot keys from `screen.active_bindings` in order, filtering out bindings whose `show` is falsy, and reuse it across the three new tests

## 3. Verification

- [x] 3.1 Run the full test suite with `pytest` and confirm all tests pass
- [x] 3.2 Manually smoke-test the TUI: focus the PR list and confirm the footer shows `q  r  o`; focus and confirm the diff pane shows `q  r  o  c  s  w`