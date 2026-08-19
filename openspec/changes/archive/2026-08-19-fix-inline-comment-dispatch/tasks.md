## 1. Fix inline comment dispatch

- [x] 1.1 Rename `on_pr_diff_view_add_comment_request` to `on_prdiff_view_add_comment_request` in `GitkeeperApp` (`gitkeeper/ui/app.py:473`) so it matches Textual's auto-computed `handler_name`
- [x] 1.2 Verify in a headless pilot run that pressing the comment action with a diff line selected opens `InlineCommentModal`

## 2. Regression test and verification

- [x] 2.1 Add a regression test in `tests/test_ui.py` that loads a diff, highlights an added line, presses the comment key, asserts `InlineCommentModal` opens, saves a comment, and asserts the `DraftReviewComment` is stored in `app.draft_comments`
- [x] 2.2 Run `uv run pytest tests -q` and verify the full suite passes
