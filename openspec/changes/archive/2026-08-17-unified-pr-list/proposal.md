## Why

The current TUI splits actionable pull requests across two separate tabs (`Queue` for scores $\ge 40$ and `Ambient` for scores $< 40$). This split adds unnecessary tab-switching friction and hides lower-scoring reviews from the primary view. Consolidating all actionable pull requests into a singular, unified list sorted strictly descending by relevance score provides immediate visibility into all incoming reviews while naturally surfacing the highest-priority PRs at the top.

## What Changes

- Replace the two-tab `Queue` / `Ambient` structure in `PRListView` with a single, continuous `OptionList` containing all actionable pull requests.
- Sort all actionable pull requests descending by `total_score` in the review list.
- Simplify selection and navigation logic: selecting any PR or using up/down arrow / j/k navigation highlights and synchronizes the overview panel without requiring tab navigation.
- Update `specs/tui-review-client/spec.md` and `specs/terminal-interface/spec.md` to remove the ambient tab/toggle requirements in favor of a singular ranked PR list.

## Capabilities

### New Capabilities
*(None)*

### Modified Capabilities
- `tui-review-client`: Update PR queue navigation requirements to specify a singular continuous list of actionable PRs sorted descending by relevance score, removing tabbed navigation between queue and ambient PRs.
- `terminal-interface`: Update review queue scenarios to reflect a singular sorted list containing all actionable review requests rather than separating below-threshold PRs into a separate tab/toggle.

## Impact

- `gitkeeper/ui/list_view.py`: `PRListView` simplified to remove `TabbedContent` (`#pr-tabs`, `#tab-queue`, `#tab-ambient`) and mount a single `OptionList(id="pr-option-list")`.
- `tests/test_ui.py`: Update UI unit and interaction tests that assert tab structure or tab switching behavior to verify the single unified list.
