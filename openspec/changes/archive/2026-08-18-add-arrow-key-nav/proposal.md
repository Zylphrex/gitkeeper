## Why

The TUI currently only accepts Vim-style `hjkl` bindings for movement and pane focus, which leaves users unfamiliar with Vim without an obvious way to navigate. Arrow keys are the universal navigation metaphor across terminal apps and should work alongside the existing Vim bindings.

## What Changes

- Add arrow key bindings (`up`, `down`, `left`, `right`) that mirror the existing `jk` movement and `hl` focus bindings in the TUI.
- Arrow keys preserve existing behavior: native widget handlers (e.g. text cursor in inputs, list scrolling) keep priority over app-level bindings.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `vim-navigation`: The existing Global Motion Keys and Focus Movement requirements are extended so arrow keys provide the same navigation as `jk` and `hl`.

## Impact

- `gitkeeper/ui/app.py` — add arrow-key entries to the app `BINDINGS` list.
- `tests/test_ui.py` — keyboard tests mirroring the existing `j/k` and `h/l` tests, using arrow keys.
- No new dependencies, no API or data changes.