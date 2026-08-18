## 1. Hyperlink Rendering

- [x] 1.1 Update `PROverviewView.update_pr` in `gitkeeper/ui/overview_view.py` to render the PR number as `[link=<url>]#<number>[/link]` when `pr.url` is present, and plain `#<number>` otherwise
- [x] 1.2 Update `PRListView._populate_list` in `gitkeeper/ui/list_view.py` to render the PR number with the Rich `link <url>` text style when the URL is present, and plain `#<number>` otherwise

## 2. Open-in-Browser Keybinding

- [x] 2.1 Add `Binding("o", "open_browser", "Open in Browser")` to `GitkeeperApp.BINDINGS` in `gitkeeper/ui/app.py`
- [x] 2.2 Implement `action_open_browser` in `gitkeeper/ui/app.py` that no-ops while a modal is open, reports "No PR selected." when nothing is selected, reports "No URL available..." when `pr.url` is falsy, and otherwise calls `self.app.open_url(pr.url)` with status bar feedback

## 3. Testing & Verification

- [x] 3.1 Add tests for the overview header hyperlink (with and without URL) in `tests/test_overview_view.py`
- [x] 3.2 Add tests for the list-row PR-number hyperlink style (with and without URL) in `tests/test_ui.py`
- [x] 3.3 Add tests for `action_open_browser`: opens URL when available, reports when URL missing, reports when nothing selected, and no-ops when a modal is open
- [x] 3.4 Run the full test suite to verify no regressions
