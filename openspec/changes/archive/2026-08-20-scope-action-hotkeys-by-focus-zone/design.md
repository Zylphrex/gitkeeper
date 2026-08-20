## Context

All six action keys are declared in `GitkeeperApp.BINDINGS` (`gitkeeper/ui/app.py:75-99`) and are therefore active in every focus zone and always listed in the footer. Textual resolves a key press against a binding chain built from the focused widget's ancestors plus the app (`.venv/.../textual/screen.py:408-446`), so any widget above the focused one can contribute bindings. A binding is enforced through `check_action` on its namespace (`GitkeeperApp`), which Textual consults both before dispatching a key (`_check_bindings` → `run_action`) and when enumerating `active_bindings` for the footer (`screen.active_bindings`). Returning `False` from `check_action` removes the binding from both paths consistently.

The app already tracks the active focus zone via `_current_zone()` and the `WIDGET_TO_ZONE` / `FOCUS_GRAPH` tables (`app.py:22-36, 357-369`). The bindings and the diff view carry their own empty-state guards (e.g. `action_hide_whitespace` reports "No PR diff loaded.").

## Goals / Non-Goals

**Goals:**
- Scope the review action keys (`c`, `s`, `w`) so they exist only while focus is in the right-hand diff zone (`file-option-list` / `diff-options`), and stop showing them in the footer outside that zone.
- Keep the change small and local to `app.py` with no layout, key-name, or footer-order changes.

**Non-Goals:**
- Not gating on whether a diff is loaded — empty/error/loading states keep the keys available in the zone and rely on existing guards.
- Not reworking the focus graph, navigation keys, or the modal flows.
- Not persisting any per-user configuration.

## Decisions

### D1: Scope via `check_action` on the app, not per-widget bindings
Implement the gate in `GitkeeperApp.check_action`: if the action name is one of `comment_action`, `submit_review`, `hide_whitespace` AND the current zone is not a right-pane zone, return `False`.

Rationale:
- Textual already treats `False` as "unavailable": the binding vanishes from `active_bindings` (footer) and the keypress is skipped (`run_action` returns `False`).
- Keeps all bindings declared in one place (`BINDINGS`), preserves today's footer ordering (`q r · c s o w` in the right zone), and needs no changes to `PRListView`, `PRDiffView`, or `modals.py`.
- The gate is naturally consistent for unfocused, shallow, and modal states, because `_current_zone()` returns `None` when the focused widget has no mapped zone, and modals live on a separate `ModalScreen` whose widgets aren't in `WIDGET_TO_ZONE`.

Alternatives considered:
- **A — move `c`/`s`/`w` onto `PRDiffView` as `"app.*"`-prefixed actions.** Also idiomatic and zone-natural, but duplicates the action-key contract in the widget, changes footer grouping/ordering depending on chain construction, and risks silently shadowing the app-level bindings for `q/r/o` if scoping the full set.
- **C — per-pane binding menus** (each pane declares its complete key set). Most self-documenting but duplicates `q`, `r`, `o` across panes and complicates the nav-key bindings, which would also need duplicating.

### Decision 2: Scoped actions live on the file list AND the diff viewer zones
`_current_zone()` returns `ZONE_RIGHT_PRIMARY` (file list) or `ZONE_RIGHT_SECONDARY` (diff) — both are "right pane". The gate treats any zone other than `ZONE_PR_LIST` as eligible. This matches the user's stated expectation that the keys are present across the whole files-and-diff pane.

### Decision 3: Existing empty-state guards remain the behavior with no diff
While the gate opens `c`/`s`/`w` in the zone regardless of load state, the existing actions already no-op politely (e.g. `hide_whitespace` prints "No PR diff loaded."). No extra state tracking is added; this keeps scope small and test behavior identical to today's right-zone behavior.

## Risks / Trade-offs

- **Zone mapping and the gate share one source of truth** — `_current_zone()` is also used by focus movement and search. the gate reads from the public helper only and never re-implements zone identity. Known side effect: if a future zone were added that should *not* expose the review actions, the gate needs an explicit allowlist instead of "not the list zone". [Low]
- **`.check_action` returns `None` in the base class by default** — the override must explicitly return `False` (not `None` or falsy accident). `None` would *dim* keys instead of hiding them; spec says hidden. Mitigated by tests asserting `False` distinctly: assert absence from footer and no-op on press. [Low]
- **Existing whitespace-toggle tests break by design** — two tests press `w` from default (PR-list) focus and now must focus a right-pane first. Plan the test updates in the same change set. [Medium]

## Migration Plan

No deployment or rollback beyond the change itself: the gate is a single override plus tests. If it mis-scopes, removing the override restores prior behavior; the affected commit stays small.