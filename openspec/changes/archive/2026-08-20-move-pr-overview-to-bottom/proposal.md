## Why

The PR overview currently occupies the far-right column, keeping it fixed at 44 columns regardless of how much horizontal space is available and wedging the description into a narrow pane alongside a full-height diff viewer. Moving the overview to a full-width fixed-height bottom row frees the diff pane to expand to the full window width and gives the PR description a much wider preview surface, with metadata and scoring rationale to its left.

## What Changes

- Move the PR overview (`PROverviewView`) from the far-right 44-column pane to a full-width bottom row.
- Split the bottom row into two columns: the metadata + score boxes on the left, the PR description markdown on the right.
- Give the bottom row a fixed height instead of `1fr`; the description is a non-scrollable preview that takes whatever width the top-row's left panes leave it.
- The PR list and diff panes expand to fill the freed horizontal space (the diff pane gains the width formerly consumed by the overview).
- The PR title (number, DRAFT badge, link) remains at the top of the bottom-left metadata column.
- Focus zones remain unchanged: the description pane is read-only and not a focus target, so `vim-navigation`'s focus graph and the `tab` cycle are untouched.

## Capabilities

### New Capabilities
- *(none)*

### Modified Capabilities
- `tui-review-client`: The overview's placement, width, and layout requirements change — the overview moves to a bottom fixed-height row, metadata stays left with the description rendering right, and the description is a non-scrollable preview rather than a scrollable section.
- `vim-navigation`: The overview description is no longer a scrollable widget, so global motion-key coverage drops it from the scrollable-widget list.

## Impact

- `gitkeeper/ui/overview_view.py`: compose layout changes from vertical stacking to a left/right split; the markdown deadline/woker mechanics stay; body scroll rendering is simplified (no `VerticalScroll` shell).
- `gitkeeper/ui/app.py`: the top-level container restructures (overview mounts as the bottom row), bottom height becomes a fixed budget; PR-list refreshes and diff selection wiring unchanged.
- `gitkeeper/ui/list_view.py`: PR list row-width budget no longer needs the right-edge `screen_width - 4` contrast with an overview column.
- `openspec/specs/tui-review-client/spec.md` and `openspec/specs/vim-navigation/spec.md`: adjusted requirement deltas.