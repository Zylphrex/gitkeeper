## Context

The right pane is currently a `TabbedContent` with two panes: "Overview" (`tab-overview`) and "Files & Diff" (`tab-diff`). The overview requires a tab switch (`1` key or clicking) to view, and cannot be seen at the same time as the diff. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- Make the selected-PR overview a persistent, fixed-width section on the far right, always visible
- Keep the Files & Diff functionality intact as the right tabbed pane
- Preserve PR selection → overview/diff synchronization and existing navigation/search behavior

**Non-Goals:**
- No changes to overview content or scoring rationale rendering
- No changes to diff viewer behavior
- No changes to review submission or commenting

## Decisions

- **Keep `TabbedContent` for Files & Diff instead of removing it entirely.** Only the "Overview" `TabPane` is removed; "Files & Diff" remains the single tab. This is the minimal change and preserves existing logic that keys off `tabs.active == "tab-diff"` (search branch, comment action, focus graph). Alternative: replace `TabbedContent` with a plain container and strip all tab checks — rejected as more invasive with the same visible result. A single-tab tab bar is acceptable; it doubles as a labeled header for the pane.
- **Render the overview as a far-right sibling in `#main-container`.** `PROverviewView` is moved out of the `TabbedContent` and yielded after it inside the top-level `Horizontal`, with a fixed width and a left border to visually separate it from the diff pane.
- **Remove `Binding("1", "tab_overview", ...)` and `action_tab_overview`.** There is no overview tab to switch to; the `2`/`tab_diff` binding remains. `action_tab_diff` becomes effectively constant since only one tab exists, but is retained for compatibility with existing callers (`action_comment_action`).
- **Focus zones.** With only `tab-diff` active, `ZONE_RIGHT_PRIMARY` resolves to `file-option-list` (the `tabs.active == "tab-diff"` branch is always taken). The overview body is treated as a read-only display, not a focus target, matching the current read-only nature of other secondary panes.

## Risks / Trade-offs

- **Fixed overview width reduces diff pane space** → Mitigation: use a modest width (~44 cols) so the diff pane retains the majority of horizontal space.
- **Single-tab `TabbedContent` shows a redundant tab bar** → Mitigation: acceptable as a pane label; a follow-up could collapse it to a plain container if undesired.
