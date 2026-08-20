## 1. GitHub fetch surface

- [x] 1.1 Add an `include_reviewed: bool = False` parameter to `GitHubGraphQLClient.fetch_pending_review_requests` in `gitkeeper/github/client.py`; when enabled, issue the additional search `is:open is:pr reviewed-by:@me archived:false` (or per-user equivalent) through the existing `extend_search` path so pagination, retry, and `seen_ids` de-duplication apply unchanged.
- [x] 1.2 Wire `config.followup.include_reviewed` through `gitkeeper/ui/app.py:action_refresh_queue` so the reviewed search runs when the option is enabled.

## 2. Classification fixes

- [x] 2.1 In `gitkeeper/scoring/calculator.py:derive_followup_state`, restrict the authored `ME_ACTIVE` "respond to review" branch to when the latest external verdict requires a response (`CHANGES_REQUESTED`) and lands after the user's latest push; an external `APPROVED` (latest verdict) SHALL classify as `WAITING_OTHERS` instead.
- [x] 2.2 Mirror the same guard in `derive_action_reasons` so the "respond to review" reason and rationale use the same response-requiring condition as the turn state.
- [x] 2.3 Extend `gitkeeper/scoring/pipeline.py:_waiting_label` so an authored `WAITING_OTHERS` item whose latest external verdict is `APPROVED` renders "approved" (waiting to merge), and only renders "awaiting reviewers" when no review verdict has been submitted.

## 3. Config

- [x] 3.1 Add `include_reviewed: bool = True` to `FollowupConfig` in `gitkeeper/config.py`.

## 4. Tests

- [x] 4.1 In `tests/test_github_client.py`, add tests that the reviewed search is issued when `include_reviewed=True`, is NOT issued when it is absent/False, and that duplicate ids across the three searches are de-duplicated (mirror the existing authored-search tests).
- [x] 4.2 In `tests/test_scoring.py`, add classification tests: authored + external `APPROVED` → `WAITING_OTHERS` labeled "approved"; authored + external `CHANGES_REQUESTED` after push → `ME_ACTIVE` "respond to review"; reviewed (non-authored) + approval then author push → `ME_ACTIVE` re-review; reviewed (non-authored) + approval, no push → `WAITING_OTHERS`.
- [x] 4.3 In `tests/test_config.py`, assert `followup.include_reviewed` defaults to `True` and parses explicit `false` from YAML.

## 5. Verification

- [x] 5.1 Run the full test suite (`pytest`) and confirm no regressions.
