## 1. Layout

- [x] 1.1 Remove the "Overview" TabPane (`tab-overview`) from `compose()` in `gitkeeper/ui/app.py`
- [x] 1.2 Yield `PROverviewView` as a far-right sibling of the `TabbedContent` inside `#main-container`
- [x] 1.3 Add fixed-width styling with a left border for `#pr-overview-view` so it reads as a distinct far-right section

## 2. Bindings, Actions, and Zones

- [x] 2.1 Remove `Binding("1", "tab_overview", "Overview")` and the `action_tab_overview` method
- [x] 2.2 Confirm `action_tab_diff` and tab-dependent logic (comment action, search branch, focus zone resolution) still work with the single remaining `tab-diff`

## 3. Tests

- [x] 3.1 Update `tests/test_ui.py` where tab switching to the overview tab is exercised (no existing tests referenced the overview tab)
- [x] 3.2 Add/verify coverage asserting the overview view is present and updates on PR selection without needing a tab switch (covered by `test_pr_list_view_and_selection`)