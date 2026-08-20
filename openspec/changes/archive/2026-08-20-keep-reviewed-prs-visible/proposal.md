## Why

Pull requests the user has already reviewed vanish from the queue once GitHub de-lists them as requested reviewers. The queue is built from `review-requested:@me` (`client.py:220`), and submitting a review — approval included — removes the user from the requested set, so an open PR that is reviewed, approved, green, and simply waiting to be merged silently disappears on the next refresh. The user wants those "waiting to be merged" items to stay visible until they actually merge, not to slip off their radar.

## What Changes

- Widen the GitHub fetch surface to also collect open pull requests the user has **reviewed** (`reviewed-by:@me`), in addition to review-requested and authored PRs, so PRs do not disappear the moment the user submits a review.
- Let the existing follow-up classifier route re-opened items correctly: a review followed by a new author push surfaces as re-review (`ME_ACTIVE`), a `CHANGES_REQUESTED` with no push back stays `WAITING_AUTHOR`, and an approval with no push back shows as `WAITING_OTHERS` ("approved") — the flat queue's `○` badge already renders this.
- Fix the authored-PR mislabel: an external **approval** of the user's own PR currently classifies as `ME_ACTIVE` "respond to review" (`calculator.py:150-155`); only a `CHANGES_REQUESTED` (or other verdict requiring a response) should trigger that state, and an approval should classify as `WAITING_OTHERS` waiting to merge.
- Add a `followup.include_reviewed` config toggle (default on, in the same spirit as `include_authored`) so the wider surface can be switched back to today's behavior.

## Capabilities

### New Capabilities
<!-- none: this extends existing fetch, scoring, config, and queue capabilities. -->

### Modified Capabilities
- `github-client`: Add a fetch path for open pull requests the user has reviewed (`reviewed-by:@me`), reusing the existing search payload, page size, pagination, and retry behavior, and merging results under the existing id de-duplication.
- `relevance-scoring`: Classify reviewed-and-approved pull requests (authored or not) as `WAITING_OTHERS` rather than dropping or mislabeling them; restrict the "respond to review" authored state to verdicts that actually require a response.
- `config-management`: Add the `followup.include_reviewed` key controlling whether reviewed pull requests are collected, default enabled, alongside the existing `include_authored`.

## Impact

- `gitkeeper/github/client.py` + `queries.py`: a third search source (`reviewed-by:@me`) reusing `REVIEW_REQUESTS_QUERY`'s payload shape.
- `gitkeeper/scoring/calculator.py`: authored "respond to review" classification keyed to response-requiring verdicts; `WAITING_OTHERS` approval path for reviewed PRs.
- `gitkeeper/config.py`: `FollowupConfig.include_reviewed` wiring and deprecation handling consistent with the existing block.
- `gitkeeper/ui/app.py` / `list_view.py`: no new rendering — the flat activity-sorted queue and `●/◇/○` badges already represent the three states; only the status-bar counts now include re-surfaced reviewed items.
- Tests under `tests/` for the reviewed fetch source, id de-duplication across the three search terms, approval classification, and config parsing.
