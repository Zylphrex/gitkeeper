## Why

The Overview panel is currently hidden behind a tab in the right pane, so reviewing a PR's context, score rationale, and body requires an extra keypress and cannot be done at the same time as inspecting the diff. Making the overview a permanent far-right section keeps PR metadata and rationale always visible while working through the review queue.

## What Changes

- Remove the "Overview" tab (`tab-overview`) from the right-side `TabbedContent`
- Render `PROverviewView` as a persistent, fixed-width section on the far right of the layout, always visible regardless of the Files & Diff pane state
- Keep the "Files & Diff" pane as the (now single) tab in the right-side tabbed content
- Remove the `1`/`tab_overview` binding and action for switching to the removed overview tab
- Keep overview selection synchronization, focus panes, and search behavior consistent with the new layout

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `tui-review-client`: the selected PR overview is displayed in a persistent far-right section instead of a tab, visible simultaneously with the Files & Diff pane

## Impact

- `gitkeeper/ui/app.py`: composer layout, `BINDINGS`, tab actions, focus/search zone handling
- `gitkeeper/ui/overview_view.py`: fixed-width styling for the far-right section
- `tests/test_ui.py`: adjust tests that interact with the overview tab
