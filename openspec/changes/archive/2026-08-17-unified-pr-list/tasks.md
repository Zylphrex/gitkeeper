## 1. UI List View Refactoring

- [x] 1.1 Refactor `PRListView` in `gitkeeper/ui/list_view.py` to remove `TabbedContent` and mount a single `OptionList(id="pr-option-list")`
- [x] 1.2 Update `set_pull_requests` in `PRListView` to sort actionable PRs descending by `total_score` and populate the unified option list
- [x] 1.3 Simplify selection preservation, highlighting, and message posting logic in `PRListView` for the single list
- [x] 1.4 Remove obsolete tab event handlers and ambient properties in `PRListView`

## 2. Testing and Verification

- [x] 2.1 Update `tests/test_ui.py` to verify ranked sorting in the single unified `PRListView` and test selection preservation
- [x] 2.2 Run full test suite with `pytest` and verify all tests pass
