## 1. Core Dispatch Framework

- [x] 1.1 Add app-level bindings to `GitkeeperApp.BINDINGS`: `j`, `k`, `h`, `l`, `gg`, `G`, `ctrl+d`, `ctrl+u`, `/`, `n`, `N`, `escape`
- [x] 1.2 Implement `action_vim_down` and `action_vim_up`: dispatch to focused widget's native cursor/scroll action based on type (OptionList → `action_cursor_down/up`, VerticalScroll → `action_scroll_down/up`)
- [x] 1.3 Implement `action_vim_top` (`gg`) and `action_vim_bottom` (`G`): dispatch to `action_first`/`action_scroll_home` or `action_last`/`action_scroll_end`
- [x] 1.4 Implement `action_page_down` (`ctrl+d`) and `action_page_up` (`ctrl+u`): dispatch to `action_page_down`/`action_page_up` on focused widget
- [x] 1.5 Guard all dispatch methods to no-op when a modal screen is active (screen is not the base screen)

## 2. Focus Movement

- [x] 2.1 Define focus zone map: widget id → zone (`pr-list`, `right-primary`, `right-secondary`) and zone → target widget id per direction
- [x] 2.2 Implement `action_focus_left` (`h`): derive current zone from focused widget, walk left in graph, `self.set_focus(target)`
- [x] 2.3 Implement `action_focus_right` (`l`): same pattern, walk right; `right-secondary` only exists when diff tab is active
- [x] 2.4 Ensure all four focus-zone widgets are focusable and can receive `set_focus`: `#pr-option-list`, `#pr-body-scroll`, `#file-option-list`, `#diff-options`

## 3. Search

- [x] 3.1 Create search overlay: an `Input` widget docked above the status bar, shown/hidden by `/` and `Escape`
- [x] 3.2 Add search state to `GitkeeperApp`: `self.search_query`, `self.search_results` (list of indices), `self.search_index`
- [x] 3.3 Implement per-zone search logic: PR list filters `active_prs` by title match; file list filters `file_diffs` by path match; diff lines highlights matches and tracks line indices
- [x] 3.4 Implement `action_next_match` (`n`) and `action_prev_match` (`N`): advance `search_index` through `search_results`, scroll/highlight the target widget at the match position

## 4. Modal Escape Handling

- [x] 4.1 Add `Escape` → `action_dismiss` binding to `InlineCommentModal` (already present via `key_escape`)
- [x] 4.2 Add `Escape` → `action_dismiss` binding to `SubmitReviewModal` (already present via `key_escape`)
- [x] 4.3 Implement app-level `action_escape`: if modal active → `pop_screen`; else if search active → clear search; else no-op

## 5. Tests

- [x] 5.1 Test `j`/`k` movement in PR list, overview body, file list, and diff viewer via `pilot.press`
- [x] 5.2 Test `gg`/`G` jump-to-top/bottom in PR list and diff viewer
- [x] 5.3 Test `Ctrl+d`/`Ctrl+u` page up/down in PR list
- [x] 5.4 Test `h`/`l` focus movement: from PR list to right pane, back, and within diff tab between file list and diff viewer
- [x] 5.5 Test `h`/`l` boundary: at leftmost pane `h` is no-op, at rightmost pane `l` is no-op
- [x] 5.6 Test `/` search in PR list filters by title; `n`/`N` navigate matches
- [x] 5.7 Test `Escape` closes modals and clears search
- [x] 5.8 Test Vim keys do not fire inside modal text areas (letters insert normally)