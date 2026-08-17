## 1. Event Handling in PRListView

- [x] 1.1 Add helper method `_handle_option_selection` to `PRListView` in `gitkeeper/ui/list_view.py`
- [x] 1.2 Implement `on_option_list_option_selected` in `PRListView` to handle click and Enter selection
- [x] 1.3 Implement `on_tabbed_content_tab_activated` in `PRListView` to update selection when switching between Queue and Ambient tabs

## 2. Testing and Verification

- [x] 2.1 Add test in `tests/test_ui.py` for clicking/selecting options via `OptionSelected`
- [x] 2.2 Add test in `tests/test_ui.py` for tab activation updating overview
- [x] 2.3 Run test suite via `pytest` and verify all tests pass
