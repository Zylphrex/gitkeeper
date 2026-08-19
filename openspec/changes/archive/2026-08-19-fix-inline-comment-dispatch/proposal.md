## Why

The inline comment flow in the TUI is dead: pressing the comment key (`c`) runs `GitkeeperApp.action_comment_action`, which posts a `PRDiffView.AddCommentRequest` message, but no handler dispatches it — the inline comment dialog never opens. Users cannot leave line-level feedback, and the entire pending-comments → review-submission path is unreachable.

Root cause: Textual auto-dispatches messages by a name computed from the declaring class via `camel_to_snake`. `camel_to_snake("PRDiffView")` yields `prdiff_view` (the leading `PR` acronym is not split), so the message's `handler_name` is `on_prdiff_view_add_comment_request`. The app instead defines `on_pr_diff_view_add_comment_request` (`gitkeeper/ui/app.py:473`), which never matches, so dispatch finds no handler and silently drops the message. The sibling `PRSelected` handler avoids this exact problem because it is explicitly annotated with `@on(PRListView.PRSelected)`; the comment handler lacks such an annotation.

## What Changes

- Rename the inline-comment message handler in `GitkeeperApp` from `on_pr_diff_view_add_comment_request` to `on_prdiff_view_add_comment_request` so it matches Textual's auto-computed `handler_name`, restoring the `c` action to open the inline comment dialog for the selected diff line.
- Add a regression test that drives the full comment flow headlessly: load a PR diff, highlight an added line, press the comment action, assert the `InlineCommentModal` opens, save a comment, and assert the text is attached as a pending `DraftReviewComment` ready for review submission.
- Leave `DiffViewer.LineCommentRequested` untouched (declared but unused; cleanup is out of scope for this change).

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `tui-review-client`: Ensure the inline comment action reliably opens the inline comment input dialog for the selected diff line and attaches the entered text as a pending comment.

## Impact

- `gitkeeper/ui/app.py`: rename `on_pr_diff_view_add_comment_request` → `on_prdiff_view_add_comment_request`.
- `tests/test_ui.py`: new regression test covering the comment action → dialog → pending draft path.
- No new dependencies; no CLI, API, or GraphQL changes.
