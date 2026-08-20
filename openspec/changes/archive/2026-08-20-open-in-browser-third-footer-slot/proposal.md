## Why

The "Open in Browser" (`o`) hot key is expected at a fixed, predictable position in the footer, but today its position depends on focus: it renders 3rd in the PR-list zone (`q  r  o`) yet 5th in the diff zone (`q  r  c  s  o  w`). The zone-scoping change introduced this position drift, so the key is inconsistent between panes.

## What Changes

- The `o` (open-in-browser) hot key SHALL always render as the third item in the footer hot-key list, in every focus zone and modal-free state.
- The footer SHALL therefore show `q  r  o` in the PR-list zone and `q  r  o  c  s  w` in the diff zone.
- The change is a position-only fix: the `o` binding key, action, description, and `show` flag are unchanged, and no other key's position or behavior changes.

## Capabilities

### New Capabilities
<!-- None: no new spec files created. -->

### Modified Capabilities
- `tui-review-client`: The open-in-browser hot key gains a fixed display position — 3rd in the footer — so it is no longer displaced by the zone-scoped review action keys.

## Impact

- `gitkeeper/ui/app.py` — reorder the `o` binding to the third slot in `GitkeeperApp.BINDINGS` (after `r`, before `c`); the footer reflects this ordering automatically via Textual's `active_bindings`.
- `tests/test_ui.py` — add footer ordering assertions to lock in the position; existing tests assert set membership only and need no semantic changes.
- No new dependencies, no layout, key-name, or modal changes.