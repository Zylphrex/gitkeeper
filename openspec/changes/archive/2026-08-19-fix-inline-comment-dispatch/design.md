## Context

See `proposal.md` — Why for the motivation.

Textual dispatches a message to a handler by `message.handler_name`, computed in `Message.__init_subclass__` from the declaring class's qualified name via `camel_to_snake`. For `PRDiffView.AddCommentRequest` this yields `on_prdiff_view_add_comment_request` (the leading `PR` acronym is not split into `pr_diff`). `GitkeeperApp._get_dispatch_methods` resolves handlers by an exact `cls.__dict__.get(method_name)` lookup walking the app's MRO, so the method name must match `handler_name` exactly or the message is silently dropped.

The app currently defines `on_pr_diff_view_add_comment_request` (`gitkeeper/ui/app.py:473`), which never matches the computed name. The sibling `PRSelected` handler avoids the issue because it is explicitly annotated with `@on(PRListView.PRSelected)` (`app.py:156`), which registers the handler without relying on the naming convention.

## Goals / Non-Goals

**Goals:**
- Restore the `c` action so that, with a diff line selected, `InlineCommentModal` opens and the saved text attaches to `self.draft_comments` as a `DraftReviewComment` available to the review-submission flow.
- Add a regression test that exercises the real dispatch path (keypress → message → handler → modal), so the naming bug cannot return silently.

**Non-Goals:**
- Removing the unused `DiffViewer.LineCommentRequested` message (`gitkeeper/ui/diff_view.py:40`).
- Changing approve/submit-review behavior, the GitHub client, or the diff parser.

## Decisions

### Decision 1: Rename the handler to Textual's computed name
Rename `on_pr_diff_view_add_comment_request` → `on_prdiff_view_add_comment_request` in `GitkeeperApp`.

*Rationale:* Directly matches the framework's auto-computed `handler_name`, which is the documented dispatch mechanism. The alternative — adding `@on(PRDiffView.AddCommentRequest)`, mirroring `app.py:156` — was considered; the user chose the rename so the handler name stays in sync with the framework's naming rule.

### Decision 2: Regression test drives the full comment flow
Add a test in `tests/test_ui.py` that constructs the app with a fake client, loads a real diff, highlights an added line in `#diff-options`, presses the comment key, asserts `InlineCommentModal` is the active screen, enters text, presses Save, and asserts the `DraftReviewComment` is pending in `app.draft_comments`.

*Rationale:* Existing modal tests only push `InlineCommentModal` directly (`tests/test_ui.py:549`, `:675`) and never exercise the `c` binding → message → dispatch path, which is exactly where the bug lived.

## Risks / Trade-offs

- **[Risk] Acronym-splitting fragility**: the renamed handler is still bound to `camel_to_snake` behavior for acronym-prefixed class names; a future Textual change to name computation could break dispatch again.
  - *Mitigation:* the regression test drives the real dispatch path, so a regression fails loudly instead of silently dropping the comment.
