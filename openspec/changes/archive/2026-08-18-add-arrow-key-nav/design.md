## Context

See proposal.md - Why. The TUI (`gitkeeper/ui/app.py`) binds Vim keys `jk` for vertical motion and `hl` for pane focus. Textual resolves a keypress to the focused widget's bindings first, falling back to the app-level bindings only when the widget does not consume the key. Widget-native arrow handling therefore wins by default, so we never override text-cursor or built-in list/scrolling behavior.

## Goals / Non-Goals

**Goals:**
- Arrow keys mirror `jk`/`hl` with no behavior divergence between the two.
- Zero new logic: reuse existing `vim_up`/`vim_down`/`focus_left`/`focus_right` actions and the existing `_guard_vim_action` modal suppression.

**Non-Goals:**
- No config toggle for vim vs arrow keys; both always active.
- No changes to `home`/`end`/`pageup`/`pagedown`, which OptionList already handles natively.
- No horizontal scroll support for long diff lines.

## Decisions

**Map all four arrows to the existing actions.** Add four entries to `GitkeeperApp.BINDINGS`: `up`→`vim_up`, `down`→`vim_down`, `left`→`focus_left`, `right`→`focus_right`. Rationale: `vim_up`/`vim_down` already dispatch to `action_cursor_up`/`action_scroll_up` (or down) based on focused widget; `focus_left`/`focus_right` already walk `FOCUS_GRAPH` with boundary guards and the `tab-diff`-active check. Reusing them guarantees arrows inherit every existing invariant.

**Add `up`/`down` bindings even though OptionList natively moves on them.** When a list is focused the native widget binding fires and the app binding never runs — behavior identical. The app-level binding only takes effect for focus states without native handling, and its presence documents intent and keeps parity explicit. No-op in the search input (dispatch catches the missing method).

**Keep `show=False`.** Consistent with the `hjkl` entries; order bindings adjacent to their Vim counterparts for readability.

## Risks / Trade-offs

- [Arrow keys inside modals reach app bindings for unfocused widgets] → Reusing existing actions preserves the modal guard; text inputs inside modals consume arrows natively anyway.
- [Search input: `up`/`down` are not natively bound by `Input`, so app bindings fire] → `_dispatch_option_or_scroll` only acts on `OptionList`/`VerticalScroll`, so this is a harmless no-op.