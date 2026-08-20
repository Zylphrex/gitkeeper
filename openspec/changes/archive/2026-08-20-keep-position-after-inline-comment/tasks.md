## 1. Shared Line Renderer

- [x] 1.1 Extract the per-line rich-text construction from `set_file_diff` (gitkeeper/ui/diff_view.py:131-161) into a `DiffViewer._render_line(idx)` helper that includes any pending comments for the line from a per-file `comments_by_line` cache.
- [x] 1.2 Rework `set_file_diff` to populate the `comments_by_line` cache from the incoming draft list and build every row through `_render_line`, keeping current visuals unchanged.

## 2. Incremental Comment Update

- [x] 2.1 Add `DiffViewer.add_pending_comment(line_no, body)`: append to the `comments_by_line` cache and swap just that row's prompt via `replace_option_prompt_at_index` so the pending label appears without rebuilding the list.
- [x] 2.2 Add `PRDiffView.add_draft_comment(path, line, body)`: append a `DraftReviewComment` to `self.draft_comments` (the authoritative list), then delegate to the current `DiffViewer` only when the displayed file's `display_path` matches `path`; otherwise no-op visually.
- [x] 2.3 Ensure line targeting in the incremental path reuses the same `new_line_no or old_line_no` identity as `get_selected_line_info` (gitkeeper/ui/diff_view.py:163-174); extract a shared helper if needed.

## 3. Wire App Save Path

- [x] 3.1 In `GitkeeperApp.on_prdiff_view_add_comment_request` (gitkeeper/ui/app.py:483-490), replace the `_display_cached_diff(pr_key)` call with `PRDiffView.add_draft_comment(event.file_path, event.line_no, body)`, keeping the status-bar message.

## 4. Tests

- [x] 4.1 Add a UI test mirroring `test_comment_action_opens_modal_and_stores_draft` (tests/test_ui.py:1010) asserting after saving: file tree highlight unchanged, diff row highlight unchanged, scroll position preserved, and the pending comment label is visible on the commented line.
- [x] 4.2 Add a cancel-dialog test asserting no draft is attached and position/focus are unchanged.
- [x] 4.3 Add a `DiffViewer`-level test that `add_pending_comment` updates only the targeted row.
- [x] 4.4 Run the full suite (`pytest tests/`) and confirm no regressions.