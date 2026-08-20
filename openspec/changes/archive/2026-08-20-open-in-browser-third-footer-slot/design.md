## Context

The footer (`Footer()` in `gitkeeper/ui/app.py:135`) renders `screen.active_bindings` in declaration order (`.venv/.../textual/widgets/_footer.py:247-256`). The app's own widgets contribute no visible bindings — every binding is declared in `GitkeeperApp.BINDINGS` (`gitkeeper/ui/app.py:77-100`), and all widget-level bindings have `show=False`. The `o` binding was appended after `submit_review`, so it renders after `c/s` — 5th — whenever `check_action` (`app.py:373-387`) exposes the review action keys in the right zone.

## Goals / Non-Goals

**Goals:**
- Make `o` render as the third visible footer item in every zone, both bindings visible.
- Keep the change to a single position move in `BINDINGS` plus ordering tests.

**Non-Goals:**
- No change to any key name, action, description, or `show` flag.
- No change to the zone-scoping gate, focus graph, navigation, or modals.
- No custom `Footer` subclass or footer-template rendering.

## Decisions

### D1: Move the `o` binding to the third slot in `BINDINGS`
- **Choice**: Reorder `GitkeeperApp.BINDINGS` so the `o` binding sits immediately after `refresh` and before `comment_action`.
- **Rationale**: The footer order is the declaration order filtered by `active_bindings`; only `c`, `s`, and `w` are ever hidden by `check_action`. Pinning `o` at declaration slot 3 therefore makes it the third *visible* item in every zone (`q r o` in the list zone, `q r o c s w` in the diff zone) with no logic changes.
- **Alternatives considered**:
  - **A — custom `Footer` render**: more control but heavy; adds a widget to maintain and would reimplement Textual ordering/grouping for no benefit.
  - **B — explicit sort key**: Textual's `Footer` has no public ordering hook; sorting would have to live in a subclass or in `active_bindings`-shimming, which is fight-the-framework for a one-line reorder.

### D2: Add exact-order footer tests
- **Choice**: Add tests asserting the exact visible footer key order (`q r o`, or `q r o c s w`) in the PR-list, `file-option-list`, and `diff-options` zones, filtering `screen.active_bindings` by `binding.show`.
- **Why**: Existing tests assert only set membership (`tests/test_ui.py:1375-1448`), so a reordering regression would pass silently. Order assertions lock in the spec's positional contract.
- **Alternative**: Rely on rendering snapshot tests — more brittle (styles/frames) and broader than needed.

## Risks / Trade-offs

- **[Risk] Future Textual version reorders bindings** → **Mitigation**: the new ordering tests exercise the actual `Footer` path (`active_bindings`), so a framework change that breaks order fails loudly and updates together with the fix.
- **[Risk] Reordering makes the `tab`/hidden bindings relative positions shift** → **Mitigation**: `show=False` bindings never render; the visible order is what the spec constrains, and tests assert exactly that.

## Migration Plan

No deployment steps beyond the change itself. Rollback is reverting the single-line reorder and the added assertions; the affected commit stays small.

## Open Questions

None.