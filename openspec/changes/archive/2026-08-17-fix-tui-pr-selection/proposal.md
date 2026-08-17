## Why

When users interact with the review queue in the TUI, selecting a PR via click or Enter key does not update the overview panel. In Textual, `OptionList` emits `OptionSelected` when an option is clicked or chosen via Enter, but `PRListView` currently only listens to `OptionHighlighted`. Additionally, switching tabs between the Queue and Ambient lists does not update the overview pane to reflect the selected tab's active PR.

Handling explicit option selection and tab switching ensures consistent, immediate synchronization across the list, overview, and diff panes regardless of input method (mouse click, Enter key, or arrow key navigation).

## What Changes

- Add event handling for `OptionList.OptionSelected` in `PRListView` so that clicking or pressing Enter on a pull request immediately triggers `PRSelected` and updates the overview and diff views.
- Add event handling for `TabbedContent.TabActivated` in `PRListView` so that switching between Queue and Ambient tabs updates the selected PR to the active tab's highlighted item.
- Add test coverage in `tests/test_ui.py` verifying that both `OptionHighlighted` and `OptionSelected` events (as well as tab switches) properly update the overview view.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `tui-review-client`: Ensure that PR selection via mouse click, Enter selection, and queue tab activation immediately synchronizes and displays the selected PR overview and diff.

## Impact

- `gitkeeper/ui/list_view.py`: Added event handlers for `OptionSelected` and `TabActivated`.
- `tests/test_ui.py`: New unit tests for click/selection and tab activation.
