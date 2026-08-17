## Context

Textual's `OptionList` emits two main interaction events:
1. `OptionList.OptionHighlighted`: Emitted when the highlight cursor changes position via arrow keys or hover.
2. `OptionList.OptionSelected`: Emitted when an option is selected (via mouse click or pressing `Enter`).

Currently, `PRListView` in `gitkeeper/ui/list_view.py` only implements `on_option_list_option_highlighted`. As a result, mouse clicks and `Enter` presses on PR list items do not propagate `PRSelected` messages to `GitkeeperApp`. Furthermore, switching tabs between the Queue and Ambient lists using `TabbedContent` does not notify the application of the newly active tab's selected item unless a highlight event is triggered afterwards.

## Goals / Non-Goals

**Goals:**
- Ensure PR selection via mouse click, Enter key, or arrow navigation consistently emits `PRSelected` and updates the Overview and Diff panes.
- Ensure switching between Queue and Ambient tabs automatically updates the selected PR to the active tab's highlighted item.
- Provide unit and integration test coverage for `OptionSelected` and `TabActivated` events.

**Non-Goals:**
- Redesigning the layout or CSS styling of the TUI panes.
- Altering the scoring algorithms or GitHub GraphQL client behavior.

## Decisions

### Decision 1: Unify Option Highlighted and Selected Handlers
We will extract the logic for resolving the PR item by index into a helper method `_handle_option_selection(list_id: str, index: Optional[int])`, and call it from both `on_option_list_option_highlighted` and `on_option_list_option_selected`.

*Rationale:* Avoids code duplication and guarantees consistent behavior whether an item is navigated with arrow keys or clicked.

### Decision 2: Listen for `TabbedContent.TabActivated`
In `PRListView`, listen for `TabbedContent.TabActivated` events on `#pr-tabs`. When activated, check the newly active tab's `OptionList.highlighted` index, post `PRSelected` with that PR, or highlight index 0 if none is highlighted.

*Rationale:* Prevents the overview and diff panes from remaining out-of-sync with the currently visible tab.

## Risks / Trade-offs

- **[Risk] Duplicate message posting when clicking an unhighlighted item**: A mouse click might fire both `OptionHighlighted` and `OptionSelected` in rapid succession.
  - *Mitigation:* `GitkeeperApp._select_pr()` is idempotent when receiving the same PR, updating the overview labels and reusing diff cache if already loaded.
