## 1. Layout: plain diff pane

- [x] 1.1 In `gitkeeper/ui/app.py`, replace the `TabbedContent`/`TabPane` wrapper around `PRDiffView` in `compose` with a plain `Vertical` container (keep id `#right-tabs`), yielding `PRDiffView` directly
- [x] 1.2 Update imports: drop `TabbedContent`/`TabPane` if unused; add `Vertical` (from `textual.containers`)

## 2. Keybinding and dead code removal

- [x] 2.1 Remove `Binding("2", "tab_diff", "Files & Diff")` from `BINDINGS`
- [x] 2.2 Remove `action_tab_diff` and its `#right-tabs` queries
- [x] 2.3 Simplify `action_comment_action` to always attach an inline comment (drop the `else: submit_review` branch)
- [x] 2.4 Remove the `_move_focus` guard checking `tabs.active != "tab-diff"` for `ZONE_RIGHT_SECONDARY`
- [x] 2.5 Verify `#right-tabs` CSS rule still applies cleanly to the plain container

## 3. Tests

- [x] 3.1 Remove the five `app.action_tab_diff()` calls in `tests/test_ui.py` (lines ~224, 387, 432, 485, 530)
- [x] 3.2 Run `pytest tests/test_ui.py` and fix any failures from the removed action
