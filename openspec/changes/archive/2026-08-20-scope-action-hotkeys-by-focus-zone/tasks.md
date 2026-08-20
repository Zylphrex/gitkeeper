## 1. Zone Gate Implementation

- [x] 1.1 Add a module-level constant `ZONE_SCOPED_ACTIONS = frozenset({"comment_action", "submit_review", "hide_whitespace"})` in `gitkeeper/ui/app.py` near the `ZONE_*` constants
- [x] 1.2 Override `GitkeeperApp.check_action(self, action: str, parameters: tuple)` so it returns `False` when the action name (dotted suffix after any `namespace.` prefix) is in `ZONE_SCOPED_ACTIONS` AND `self._current_zone()` is not one of the two right-pane zones (`ZONE_RIGHT_PRIMARY`, `ZONE_RIGHT_SECONDARY`)
- [x] 1.3 For every non-scoped action (including `q`, `r`, `o`, and all navigation keys), delegate to `super().check_action(action, parameters)` so existing behavior and footer state are unchanged
- [x] 1.4 Confirm scope is zone-based only: `ZONE_PR_LIST` and any `None`/modal focus state gate the keys regardless of whether a diff is loaded

## 2. Test Updates

- [x] 2.1 Add a test asserting that with focus in the PR list zone, `GitkeeperApp.screen.active_bindings` does not contain keys `c`, `s`, or `w`, and does contain `q`, `r`, `o`
- [x] 2.2 Add a test asserting that with focus in `#diff-options` (right zone), all of `q`, `r`, `c`, `s`, `o`, `w` appear in `screen.active_bindings`
- [x] 2.3 Add a test asserting the same scoping for `#file-option-list` focus (file tree zone)
- [x] 2.4 Add a test that pressing `w` from the PR list zone leaves `hide_whitespace` unchanged and the status bar unchanged (no-op)
- [x] 2.5 Add a test that pressing `c` from the PR list zone does not open `InlineCommentModal`
- [x] 2.6 Add a test that pressing `s` from the PR list zone does not open `SubmitReviewModal`
- [x] 2.7 Add a test that the modal state also hides the scoped keys: while `SubmitReviewModal` is open (or with an unfocused widget), `active_bindings` excludes `c`, `s`, `w`

## 3. Update Existing Tests That Assumed Global Scope

- [x] 3.1 Update `test_hide_whitespace_toggle_keeps_real_changes` (tests/test_ui.py:1362) to focus `#diff-options` (or `diff_options.focus()`) before pressing `w`
- [x] 3.2 Update `test_hide_whitespace_noop_without_loaded_diff` (tests/test_ui.py:1383) to focus a right-pane widget before pressing `w`, so the "No PR diff loaded." guard is exercised from an eligible zone
- [x] 3.3 Audit the rest of `tests/test_ui.py` for any other `press("c"/"s"/"w")` from default PR-list focus and add a focus step where needed

## 4. Verification

- [x] 4.1 Run the full test suite (`pytest`) and confirm all tests pass
- [x] 4.2 Manually smoke-test the TUI: focus the PR list and confirm the footer shows only `q  r  o`; focus the diff pane and confirm all six keys appear and `c`/`w` work