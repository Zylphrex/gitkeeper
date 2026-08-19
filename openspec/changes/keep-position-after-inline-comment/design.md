## Context

See proposal.md — Why. The diff pane today renders one file at a time: `PRDiffView` holds the parsed `file_diffs` and the pending `draft_comments` list; `DiffViewer` renders the current file's lines into an `OptionList` (`#diff-options`) with a "💬 Pending Comment" label appended to any commented line (gitkeeper/ui/diff_view.py:131-161).

Saving an inline comment in the app currently appends the draft and calls `_display_cached_diff`, which fully re-parses the diff and re-renders the file tree, resetting the selected file to the first leaf and the line highlight to the top of the file. Textual `OptionList` (8.2.8) exposes `replace_option_prompt_at_index(index, prompt)` which swaps a single row's prompt in place without rebuilding the list.

## Goals / Non-Goals

**Goals:**
- Preserve file tree selection, line highlight, scroll position, and focus when a comment dialog closes (save or cancel).
- Show the pending comment label on the commented line immediately after saving.
- Keep a single source of truth for pending comments per PR so submission behavior is unchanged.

**Non-Goals:**
- Changing the pending comment data model, batching, or GitHub submission flow.
- Preserving position on PR switch or queue refresh (a full reload there is correct).
- Editing or deleting existing pending comments.

## Decisions

### 1. In-place single-row update rather than full reload (Option B)
- **Decision**: After saving a comment, do not reload the diff. Appends the comment to the authoritative list, then updates only the commented line's row prompt in the displayed file.
- **Rationale**: Position preservation is a side effect of nothing-else-moving. The full reload path resets tree selection and scroll by construction, and would need extra restore logic (Option A).
- **Alternative considered**: Snapshot `(file, line)` before reload, restore after (Option A). Rejected: more state juggling, and rebuilding OptionList rows can still disturb scroll/focus.

### Decision 2: Single shared line renderer
- **Decision**: Extract the per-line rich-text construction currently inline in `set_file_diff` (diff_view.py:131-161) into a `_render_line(idx)` helper. Both the full render path and the incremental per-line update call it so the pending-comment label renders identically.
- **Rationale**: Avoids two diverging renderings of a line (with/without comments).

### Decision 3: Comment cache lives in the viewer, list ownership stays at PR level
- **Decision**: `PRDiffView` keeps the authoritative `draft_comments` list (as today). `DiffViewer` holds a per-file `comments_by_line` cache populated from that list in `set_file_diff`. When a comment is saved, `PRDiffView.add_draft_comment(path, line, body)` appends to the list, then — only if the commented file is the one currently displayed — delegates `DiffViewer.add_pending_comment(line_no, body)` which mutates the cache and swaps that row's prompt in place.
- **Rationale**: The file is always displayed when the user comments on it, so the row exists and the visual update applies. If the target line ever cannot be matched in the rendered rows, the update silently no-ops and the label naturally appears on the next render of that file.

## Risks / Trade-offs

- **[Risk] Row height change on incremental update** → The pending label can add a line to the swapped row, shifting content below it visually. This matches today's full-render behavior, and the `OptionList` reflows content deterministically. **Mitigation**: verify with the snapshot tests.
- **[Risk] Unmatched line on incremental update** → If a comment's target line maps to no rendered row (duplicate line numbers, edge mismatch between old/new line numbers), the row isn't updated but the comment still attaches and appears when that file re-renders. **Mitigation:** accept the degradation and cover it with tests.

## Migration Plan

No deployment or rollback steps: this is an in-app behavior change with no stored state.