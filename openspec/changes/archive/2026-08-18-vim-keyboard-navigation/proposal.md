## Why

The TUI already supports keyboard navigation for some actions (q, r, 1, 2, c, a, s), but movement is limited to arrow keys and Tab. Vim users—a core audience for terminal tools—expect home-row navigation (`j/k` for up/down, `h/l` for focus movement, `gg/G` for jumps, `/` for search). Adding systematic Vim-like navigation makes the app feel native to terminal power users, reduces hand movement, and differentiates GitKeeper from basic TUI tools.

## What Changes

- **Global `j/k` navigation**: up/down movement in any scrollable or list widget (PR list, overview body, file list, diff lines)
- **Global `h/l` focus movement**: move focus left/right between panes
- **`gg`/`G` jumps**: jump to top/bottom of focused widget
- **`Ctrl+d`/`Ctrl+u` paging**: half-page scroll up/down
- **`/` search**: filter/search within the focused widget's context
- **`n`/`N`**: next/previous search result
- **`Escape`**: unified cancel/close/clear
- Consistent focus tracking across all five focus zones: PR list, overview body, file list, diff viewer, and modals
- Existing bindings (q, r, 1, 2, c, a, s, Tab) preserved

## Capabilities

### New Capabilities
- `vim-navigation`: systematic Vim keyboard navigation across all TUI widgets, including motion keys, focus movement, search, and escape handling

### Modified Capabilities
- `tui-review-client`: update requirements for queue navigation, diff navigation, and commenting to reflect the new Vim keybindings and focus model

## Impact

- `gitkeeper/ui/app.py`: add new bindings, focus graph, search state, and escape handler
- `gitkeeper/ui/list_view.py`: ensure `j/k` works for PR list navigation, add `gg`/`G` support
- `gitkeeper/ui/overview_view.py`: ensure `j/k` scrolls the body, add `gg`/`G`/`Ctrl+d`/`Ctrl+u` support
- `gitkeeper/ui/diff_view.py`: ensure `j/k` navigates file list and diff lines, `h/l` switches between them, `gg`/`G`/`Ctrl+d`/`Ctrl+u` support
- `gitkeeper/ui/modals.py`: ensure Escape closes modals, Vim keys pass through
- No new dependencies, no API changes, no config changes