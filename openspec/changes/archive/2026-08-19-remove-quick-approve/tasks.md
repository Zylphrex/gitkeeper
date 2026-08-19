## 1. Remove quick-approve binding and action

- [x] 1.1 In `gitkeeper/ui/app.py`, remove `Binding("a", "quick_approve", "Approve")` from `BINDINGS` (line 78) — this also drops its footer entry
- [x] 1.2 Remove the `action_quick_approve` method in `gitkeeper/ui/app.py` (line 491)
- [x] 1.3 Verify `_submit_review_worker` remains reachable only from `action_submit_review` and that no imports become orphaned

## 2. Tests

- [x] 2.1 Grep `tests/` for `quick_approve`, `action_quick_approve`, and any keypress test binding `"a"`; remove or update any that assume the shortcut exists
- [x] 2.2 Run `pytest` and confirm the full suite passes with the quick-approve path removed
