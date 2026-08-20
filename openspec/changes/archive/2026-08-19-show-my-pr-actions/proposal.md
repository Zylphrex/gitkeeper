## Why

Reviewers lose track of what they have already done on a pull request between sessions: whether they approved it, requested changes, left inline comments, or are re-reviewing after a new push. The TUI already fetches this data (review records carry author/state/timestamp, thread comments carry authorship) and the scoring layer already derives the viewer's verdict, but nothing surfaces it as an explicit per-PR status.

## What Changes

- Add a "you" status line to the PR overview panel that states the viewer's own actions on the selected PR: not yet reviewed, approved, requested changes, or commented — with a relative time for the latest action and a re-review indicator when the author pushed after it.
- Distinguish the viewer's own comments from others' in the diff thread view (label/emphasize threads authored by the viewer), so scrolling a diff instantly reveals where they have already spoken.
- Include in-session pending draft comment counts in the "you" status so drafts are not silently lost when moving between PRs.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `tui-review-client`: add a viewer-action status line to the PR overview and distinguish the viewer's own diff-thread comments from other reviewers'.

## Impact

- `gitkeeper/ui/overview_view.py`: render the new "you" status line from review records, thread data, and draft-comment state.
- `gitkeeper/ui/diff_view.py`: style thread labels for comments authored by the current viewer.
- `gitkeeper/ui/app.py`: pass the viewer login and draft-comment state to the relevant views.
- `gitkeeper/scoring/calculator.py`: expose the viewer's latest verdict and its timestamp to the UI (derivation logic largely exists; needs a small public accessor).
- No new GitHub data is required: `reviews` and `reviewThreads` already carry author fields.