## Context

See proposal.md - Why. The right panel is a `TabbedContent` with exactly one `TabPane` ("Files & Diff", `tab-diff`) wrapping `PRDiffView`, plus a `Binding("2", "tab_diff", "Files & Diff")`. A handful of handlers branch on `tabs.active == "tab-diff"`; with one tab those branches are constant. The archived `2026-08-18-overview-as-right-section` design explicitly flagged collapsing the single-tab bar as an acceptable follow-up.

## Goals / Non-Goals

**Goals:**
- Remove the `2` keybinding for Files & Diff (and its footer entry)
- Remove the "Files & Diff" tab bar/label so the diff renders as a plain pane
- Strip the now-dead tab-state machinery (`action_tab_diff`, tab guards) and update tests

**Non-Goals:**
- No change to diff viewer, file list, diff lines, or search behavior
- No change to Overview rendering or focus zones/graph shape
- No change to `s`/`a` review submission

## Decisions

- **Replace `TabbedContent` with a plain `Vertical` container keeping id `#right-tabs`.** The single `TabPane` is dropped; `PRDiffView` is yielded directly inside the container. Keeping the id means the existing CSS rule `#right-tabs { width: 1fr; height: 1fr; }` carries over unchanged. *Alternative rejected:* keep `TabbedContent` and hide its tab bar via CSS — this leaves an always-inert widget, the tab-active guards, and the `2` binding in place for no benefit.
- **Remove `Binding("2", "tab_diff", "Files & Diff")` and `action_tab_diff`.** The key had no function once the only tab is always active. *Alternative rejected:* keep the binding as a no-op for key compatibility — the `2` key has no documented contract in the vim-navigation spec and tests never press it.
- **Simplify `action_comment_action` to always attach an inline comment.** The `else: action_submit_review()` branch only fired when `tabs.active != "tab-diff"`, which is impossible with one tab. `c` always means inline comment on a line; review submission stays on `s`/`a`.
- **Remove the `_move_focus` guard** (`if tabs.active != "tab-diff": return`) before moving to `ZONE_RIGHT_SECONDARY`. It is dead; the focus graph already routes right-primary → right-secondary correctly.
- **Drop `app.action_tab_diff()` calls in `tests/test_ui.py`.** `PRDiffView` is mounted unconditionally in `compose`, so the calls were needed only to activate the tab render; with a plain pane they are no-ops. The five sites (lines ~224, 387, 432, 485, 530) simply lose that line.

## Risks / Trade-offs

- **Removing the `2` binding could be surprising to muscle memory** → Mitigation: the key is being freed, and focus movement is already covered by `h`/`l`/Tab; footer no longer advertises a shortcut that does nothing.
- **`action_comment_action` loses its fallback surface** → Mitigation: the fallback was unreachable; `s` (submit review modal) and `a` (quick approve) remain the review-entry paths, and the "no line selected" behavior is unchanged.
