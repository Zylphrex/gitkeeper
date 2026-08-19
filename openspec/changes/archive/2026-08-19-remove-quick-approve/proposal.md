## Why

The `a` quick-approve shortcut submits an APPROVE review (with an `"LGTM!"` body and any pending inline comments) to GitHub on a single keystroke with no confirmation. It is the only review path that fires an irreversible, public side effect without an explicit submission gesture — `s` already forces confirmation via the review modal. The spec itself says approval happens only "and confirms submission", so the shortcut violates the documented contract, and a misfired approval permanently marks a PR as reviewed.

## What Changes

- Remove the `a` keybinding (`Binding("a", "quick_approve", "Approve")`) and its footer entry.
- Remove `action_quick_approve` from `gitkeeper/ui/app.py`; approval flows exclusively through the `s` submit-review modal, which requires an explicit submission gesture.
- Keep `_submit_review_worker` and the pending inline-comment bundling, which remain in use by `action_submit_review`.
- Remove any remaining references to the quick-approve action in tests or docs.

## Capabilities

### New Capabilities
_(none)_

### Modified Capabilities
- `tui-review-client`: the system no longer provides a one-key permissionless approve action. Approving a review requires the submit-review flow, which prompts the user to choose the verdict and confirm submission before the approve review is sent to GitHub.

## Impact

- `gitkeeper/ui/app.py`: `BINDINGS` (remove `a`), footer entry, `action_quick_approve` removed. `action_submit_review` and `_submit_review_worker` unchanged.
- `tests/test_ui.py`: remove/add any call sites that reference the `a` quick-approve action (grep shows no current references; verify before editing).
- `gitkeeper/github/client.py`: unchanged — the `add_pull_request_review` mutation still serves the `s` flow.
