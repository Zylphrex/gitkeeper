## Context

Currently, `gitkeeper/ui/list_view.py` utilizes Textual's `TabbedContent` with two tabs (`#tab-queue` and `#tab-ambient`) to split pull requests based on whether their `score.total_score >= min_threshold` (default 40). Both tabs contain separate `OptionList` instances (`#queue-option-list` and `#ambient-option-list`), requiring tab change event handlers, dual option event handling, and conditional selection preservation logic.

## Goals / Non-Goals

**Goals:**
- Replace the dual-tab container in `PRListView` with a single, direct `OptionList(id="pr-option-list")`.
- Sort all actionable PRs descending by relevance score (`total_score`).
- Preserve the highlighted/selected PR across queue background refreshes via a single list lookup.
- Simplify keyboard and mouse navigation without tab-switching handlers or tab-change synchronization bugs.

**Non-Goals:**
- Changing the underlying relevance score calculation or actionability gates in `scoring/`.
- Adding visual section headers or multi-column sort tables (preserving a clean, single continuous list).

## Decisions

### Decision 1: Direct Single `OptionList` Container
- **Choice**: Replace `TabbedContent` with a direct `OptionList(id="pr-option-list", classes="pr-option-list")`.
- **Rationale**: Eliminates unnecessary DOM nesting, removes tab-switching event handlers (`on_tabbed_content_tab_activated`), and makes key navigation intuitive.
- **Alternatives Considered**: Keeping a single tab inside `TabbedContent` (unnecessary visual chrome and widget overhead).

### Decision 2: Descending Sort by Total Score
- **Choice**: Filter actionable PRs (`p.is_actionable`) and sort by `p.score.total_score` descending (`reverse=True`).
- **Rationale**: Highest relevance reviews naturally rise to the top. When scores tie, original query order / PR number is preserved.

### Decision 3: Simplified Selection Preservation
- **Choice**: When `set_pull_requests(scored_prs, preserve_pr_key)` is called, iterate through the single sorted `active_prs` list to match `key == f"{p.pr.repo_name_with_owner}#{p.pr.number}"`. If found, set `highlighted` to that index. Otherwise, default to index `0`.
- **Rationale**: Eliminates branching across two lists and tabs while reliably restoring the user's focus on background refreshes.

## Risks / Trade-offs

- **[Risk] Large number of low-relevance PRs in list** → Mitigation: All items are scrollable via standard `OptionList` virtual scrolling with fast keyboard navigation (`Home`, `End`, `PageUp`, `PageDown`, arrow keys). Score badges are clearly visible to distinguish priority.
