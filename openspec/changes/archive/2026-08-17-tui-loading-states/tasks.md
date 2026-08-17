## 1. Top Header Component

- [x] 1.1 Implement `AppHeader` widget in `gitkeeper/ui/header.py` with title, activity status indicator, and last refreshed timestamp display
- [x] 1.2 Export `AppHeader` from `gitkeeper/ui/__init__.py` and integrate it into `GitkeeperApp` layout in `gitkeeper/ui/app.py`

## 2. Diff View Loading States

- [x] 2.1 Add loading and error state management to `PRDiffView` in `gitkeeper/ui/diff_view.py`
- [x] 2.2 Wire up asynchronous diff fetch triggers and callbacks in `GitkeeperApp._fetch_diff_for_pr` to toggle `PRDiffView` loading states

## 3. Non-Blocking Refresh Flow & Selection Preservation

- [x] 3.1 Update `GitkeeperApp.action_refresh_queue` to report granular progress steps to `AppHeader` and update the completion timestamp
- [x] 3.2 Update `PRListView` and `GitkeeperApp._load_scored_prs` to preserve the currently selected PR across list refreshes when present

## 4. Testing & Verification

- [x] 4.1 Add unit and component tests in `tests/test_ui.py` for `AppHeader` status updates and timestamp formatting
- [x] 4.2 Add tests for `PRDiffView` loading states and error handling
- [x] 4.3 Add tests for non-blocking queue refresh and selection preservation
