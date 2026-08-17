## 1. UI Implementation

- [x] 1.1 Update `render_pull_requests_table` in `gitkeeper/ui/table.py` to format PR numbers with `[link=URL]#<number>[/link]` when `pr.url` is present
- [x] 1.2 Verify fallback to plain text `#{pr.number}` when `pr.url` is empty or None

## 2. Testing & Verification

- [x] 2.1 Add unit tests for table rendering with PR hyperlinks in `tests/test_cli.py` or new `tests/test_ui.py`
- [x] 2.2 Run test suite to verify no regressions
