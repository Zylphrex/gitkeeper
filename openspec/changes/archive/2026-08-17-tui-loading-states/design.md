## Context

See `proposal.md` for problem background. The current TUI uses Textual's default `Header` and reports background updates via a single bottom status `Label`. When background refresh or diff fetching takes place, there is no high-visibility status indicator, no tracking of refresh timestamps, and the diff view can show stale or empty views while network requests run in worker threads.

## Goals / Non-Goals

**Goals:**
- Replace or enhance the top header with a custom `AppHeader` widget showing:
  - Application title (`gitkeeper`)
  - Live activity status indicator (e.g., `⠋ Fetching from GitHub...`, `⠋ Evaluating heuristics...`)
  - Formatted "Last refreshed: HH:MM:SS" timestamp
- Implement non-blocking background queue refresh maintaining list interaction and preserving currently selected PR if still present in the queue.
- Implement explicit loading indicators and error states in `PRDiffView` during patch retrieval.

**Non-Goals:**
- Automatic background polling / timer-based periodic auto-refresh (refresh remains user-triggered or on-launch).
- Offline caching of diffs to disk.

## Decisions

### Decision 1: Custom `AppHeader` Widget vs. Subtitle Mutation on Standard `Header`
- **Choice**: Implement a dedicated `AppHeader(Widget)` containing sub-components (title label, status/spinner container, timestamp label).
- **Rationale**: Textual's built-in `Header` provides limited layout control for multi-column metadata (left title, center dynamic status with styling/spinner, right timestamp). A custom widget gives clean CSS layout (`Horizontal` container with dock top).
- **Alternatives Considered**: Modifying `app.sub_title` dynamically on Textual's standard `Header`. While simpler, it lacks fine-grained styling and flexible layout for separate status messages and timestamps.

### Decision 2: Reactive State Management for Diff Loading
- **Choice**: Use a reactive `loading` state in `PRDiffView` that mounts a `LoadingIndicator` or placeholder message in the diff container until `load_diff()` is invoked.
- **Rationale**: Prevents displaying stale diffs from previously inspected PRs while the network fetch is executing.
- **Alternatives Considered**: Blanking out the diff view without any indicator. This would lead to ambiguity on whether the PR has zero changes or is still fetching.

### Decision 3: Background Worker Thread Communication
- **Choice**: Use Textual's `@work(exclusive=True, thread=True)` with step-by-step UI callbacks via `self.app.call_from_thread` to update `AppHeader` and `status_bar`.
- **Rationale**: Keeps network I/O and local git heuristics off the main asyncio event loop without blocking user navigation.

## Risks / Trade-offs

- **[Risk] Selection loss on queue refresh** → If the PR list is replaced, index-based highlighting may reset to 0.
  - *Mitigation*: Track currently selected PR identifier before updating options and restore selection if the PR is still present in the refreshed list.
- **[Risk] Race condition on rapid PR diff switching** → Switching between multiple PRs in rapid succession could resolve diff network requests out of order.
  - *Mitigation*: Ensure exclusive worker handling or verify that incoming diff responses match `self.current_scored_pr` before rendering.
