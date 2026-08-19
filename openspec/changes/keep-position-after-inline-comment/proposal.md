## Why

After saving an inline diff comment, the diff pane fully reloads and drops the reviewer back to the first changed file at the top of the file, losing the file, line, and scroll position they were just working in. Reviewing flows involve many comments per file; resetting position after every comment makes the flow tedious and disorienting.

## What Changes

- Replace the full diff reload after saving an inline comment with an in-place, single-line update that appends the pending comment label to the commented line.
- Preserve the current state when the comment modal closes: file tree selection, diff line highlight, scroll position, and focus.
- Keep the pending comment lifecycle unchanged: comments remain drafts in memory and are included in the next review submission.
- Keep the full diff reload for its legitimate uses: switching PRs and refreshing the queue.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `tui-review-client`: Extend the "Inline and Top-Level Commenting" requirement — when an inline comment is saved, the system SHALL preserve the reviewer's position in the diff view instead of resetting the file selection and scroll.

## Impact

- `gitkeeper/ui/app.py`: `handle_comment_result` no longer triggers a full diff reload after saving a comment.
- `gitkeeper/ui/diff_view.py`: `DiffViewer` gains an incremental single-line update path (an extracted per-line renderer shared with the full render path); `PRDiffView` exposes the incremental comment insertion.
- Textual 8.2.8 `OptionList.replace_option_prompt_at_index` used for the in-place row swap.
- Tests under `tests/` coverage for diff rendering and comment flow.