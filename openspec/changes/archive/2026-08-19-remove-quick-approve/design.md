## Context

See proposal.md - Why. The app binds `Binding("a", "quick_approve", "Approve")` (`gitkeeper/ui/app.py:78`) and its handler `action_quick_approve` (line 491) posts an APPROVE review to GitHub without any confirmation, bundling any pending inline comments. The `s` submit-review path (`action_submit_review` → `SubmitReviewModal` → `_submit_review_worker`) already requires an explicit verdict choice and submission click. The spec (`tui-review-client`) already stated approval must be confirmed, so this change deletes the non-conforming path rather than adding a new dialog.

## Goals / Non-Goals

**Goals:**
- Remove the `a` quick-approve binding and its footer entry
- Remove `action_quick_approve` so no code path posts a review without confirmation
- Leave the `s` flow and `_submit_review_worker` untouched

**Non-Goals:**
- No new confirmation dialog — the existing `SubmitReviewModal` is the single submission channel
- No change to `_submit_review_worker`, the GitHub client, or pending inline-comment handling
- No change to the `s`/`c`/`o` bindings or their handlers

## Decisions

- **Remove the `a` binding entirely rather than remap or keep it as a no-op.** The binding's three values (`a`, `quick_approve`, `Approve`) exist to advertise a shortcut; once the action is gone, keeping the key mapped to nothing would leave a stale footer entry and a dead handler. *Alternative rejected:* keep `a` as a fallback to `action_submit_review()` — that is just a longer spelling of `s` and adds a divergent code path for no behavioral benefit.
- **Approval now requires exactly two gestures via `s`:** open the modal (Approve radio is pre-selected by default) and press "Submit Review". This preserves an acceptable fast path while enforcing the confirmation the spec mandates. *Alternative rejected:* add a new lightweight confirm modal for `a` — reintroduces a second submission surface we are trying to eliminate.
- **`_submit_review_worker` and its signature stay unchanged.** `s` remains its sole caller; deleting `action_quick_approve` removes the only other reference. The default `"LGTM!"` body disappears with `a`; users may leave the modal's summary blank (submitted as `body=None`).
- **Update tests defensively.** Grep found no current test reference to `action_quick_approve`/`quick_approve` in `tests/`; the task is to re-verify and, if any keypress or call-site tests depend on the `a` binding, drop them.

## Risks / Trade-offs

- **Muscle memory: users reaching for `a` now get nothing** → Mitigation: the footer stops advertising the shortcut immediately, and the pre-selected Approve radio in `s` keeps the intent one step away. The key is left unmapped rather than reassigned so nothing surprising happens.
- **Slightly slower bulk-approval flow** → Mitigation: acceptable trade-off; the tool's value is decision quality, not throughput, and the option to leave the body blank keeps the modal lightweight.
