## Context

See proposal.md for motivation. GitKeeper is a Textual TUI (Python >=3.10, Textual >=0.50). The UI surface is four focusable content widgets plus modals:

- `#pr-option-list` (OptionList) — PR queue, left pane
- `#pr-body-scroll` (VerticalScroll wrapping a Markdown widget) — overview body, right pane
- `#file-option-list` (OptionList) — changed files, right pane diff tab
- `#diff-options` (OptionList) — diff lines, right pane diff tab
- `InlineCommentModal` / `SubmitReviewModal` — modal screens with text input

Existing app-level bindings (app.py:46-55): `q`, `r`, `tab`, `1`, `2`, `c`, `a`, `s`. Movement today relies on arrow keys and Tab focus cycling. Textual has no native mode system. `j`/`k` are not bound by OptionList or VerticalScroll, so they bubble to the App — the app-level dispatcher pattern is viable without widget subclassing.

## Goals / Non-Goals

**Goals:**
- One global, modeless keymap covering motion (`j/k`, `gg`, `G`, `Ctrl+d/u`), focus (`h/l`), search (`/`, `n`, `N`), and cancel (`Escape`)
- Consistent behavior across all four focus zones with a single implementation
- Preserve all existing bindings and arrow-key/mouse navigation
- Keep focus and search state in one place (the App) so future panes are cheap to add

**Non-Goals:**
- True Vim modes (no insert/visual/command mode state machine)
- Vim motions inside modal text areas (comment/review text stays normal text editing)
- User-configurable keymaps
- Visual selection, yanking, or macros

## Decisions

### D1. Modeless app-level dispatcher for j/k
Bind `j`/`k` (and `gg`, `G`, `Ctrl+d/u`) at the App level, not on individual widgets. `action_vim_down`/`action_vim_up` inspect `self.screen.focused` and dispatch to the focused widget's native action:

| Focused widget | down/up | top/bottom | page down/up |
|---|---|---|---|
| OptionList | `action_cursor_down/up` | `action_first`/`action_last` | `action_page_down/up` |
| VerticalScroll | `action_scroll_down/up` | `action_scroll_home`/`action_scroll_end` | `action_page_down/up` |

Rationale: OptionList and VerticalScroll already implement the underlying motions; we just expose Vim keys. Alternatives considered:
- Widget-subclass bindings per widget → duplicates logic across four widgets.
- Switching OptionList → ListView → churn, loses Option API, and doesn't fix the overview scroll.
- True modal system → rejected per non-goals.

### D2. Centralized focus graph with derived zone from focused widget
Define three zones and a map from widget id → zone:

```
pr-list ──l──→ right-primary ──l──→ right-secondary   (right-secondary only exists in diff tab)
    ↑ h            ↑ h                  ↑ h
```

`action_focus_left`/`action_focus_right` derive the current zone from `self.screen.focused`'s id (or a lookup dict), walk the graph in the requested direction, and call `self.set_focus(...)` on the target widget. Boundary moves (leftmost/rightmost) are no-ops. When the diff tab is inactive, `right-primary` maps to `#pr-body-scroll` and `right-secondary` does not exist, so `l` from the body is a no-op.

Rationale: explicit, testable, and mirrors the visual layout so `h`/`l` feel directional. Alternatives considered:
- Tab-order cycling → Textual already provides this; doesn't satisfy "directional".
- DOM-geometry computation (`screen.find_widget`) → fragile across layouts.

Tab/Shift+Tab remain active as the flat cycle; `h`/`l` coexist with them.

### D3. Search as an app-managed overlay driven by the focused zone
`/` opens a small search `Input` overlay (docked above the status bar), focused automatically. On Enter, the query is applied per zone:

- PR list: filter `active_prs` by title match and repopulate; Esc restores the unfiltered list (search state kept on the App)
- File list: filter `file_diffs` by path match
- Diff lines: keep all lines, track match line indices for `n`/`N` jumping and highlight matches

`n`/`N` move through `self.search_results` (a list of indices into the current zone's items) and set the widget's highlighted/scroll position. The search query and result index live on the App (`self.search_query`, `self.search_results`, `self.search_index`), cleared on Escape or when the focused zone changes.

Rationale: search needs per-zone result semantics (filter vs jump), so a single app-owned state object with a small per-zone apply function keeps it unified without widget sprawl.

### D4. Escape as a layered cancel
`Escape` is handled by an app-level `action_escape`:

1. If a modal screen is active → `self.pop_screen()` (modal dismissed without result)
2. Else if search is active → clear search overlay and restore list state
3. Else → no-op

Modal screens (`InlineCommentModal`, `SubmitReviewModal`) additionally bind `Escape` to `dismiss` so behavior holds regardless of focus. Rationale: Escape has one meaning ("get out of the current context") and layering gives a deterministic order. Textual's own Escape handling on screens must be verified and overridden where it conflicts.

### D5. Search disabled in modal text areas
Vim keys (`j/k/h/l`, `gg`, etc.) must not fire while a modal's TextArea/RadioSet has focus. Since bindings are app-level, guard all `action_vim_*`/`action_focus_*` methods: if the focused widget is inside a modal (screen is not the base screen), return early. Rationale: typing `j` in a comment body must insert "j", not scroll.

## Risks / Trade-offs

- [Focus graph drift when new panes are added] → Centralize the zone map and its widget lookups in one module-level structure; document that new focusable panes must register there.
- [App-level j/k vs future Textual defaults] → Textual may later bind j/k on OptionList/VerticalScroll; guard dispatch to avoid double-stepping and keep a UI test that asserts single-step movement.
- [Chord reliability for gg in some terminals] → Textual handles multi-key chords internally; add a test using the pilot to press `g,g`, and document the combo in the footer/help.
- [Filtering on search can lose the preserved PR selection across refresh] → Keep selection-preservation logic (`_load_scored_prs`) working on the unfiltered list and re-apply the active filter after refresh.
- [Escape collisions with Textual modal defaults] → Verify Textual's behavior for `Escape` on pushed screens and pin `Escape` → dismiss explicitly on modal screens.

## Migration Plan

No data or config migration. Rollback is a git revert of the bindings/dispatch changes. Deploy as part of the normal TUI release.

## Open Questions

None that would change the specs or approach.