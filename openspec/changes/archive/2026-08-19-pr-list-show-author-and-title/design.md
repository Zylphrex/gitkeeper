## Context

The PR queue panel is `width: 42` (list_view.py CSS), leaving ~40 usable columns per row after the border and list padding. Today each entry wastes line 1 (`[T0] #401 astra-core` occupies ~20 of 40 columns) while line 2 crams a hard-coded `title[:22]` slice together with a `(reason)` chip — the combined text exceeds the width, wraps mid-chip, and garbles the title (`fix: restore the consi`). Motivation and scope: see proposal.md — Why.

Layout context: `PRListView(42) | diff-pane(1fr) | overview(44)` (app.py). The diff pane is already the squeezed column at narrow terminals, so this design reallocates the list's *existing* row budget rather than requesting more width.

## Goals / Non-Goals

**Goals:**
- Every queue entry shows tier, PR number, repository, and author `@login`.
- The title gets maximal width: its own line, flush-left, ellipsis-truncated, never wrapped.
- Rows stay exactly two lines so queue skimming and `j`/`k`/`gg`/`G` paging keep uniform geometry.

**Non-Goals:**
- No layout-width changes (list stays 42, diff pane untouched).
- No adaptive width measurement (constant `ROW_WIDTH`, explained below).
- No draft badge in the list (stays overview-only).
- No changes to scoring reasons — they remain in the overview rationale only.

## Decisions

### 1. Author joins line 1; title takes line 2 alone
Line 1 hosts everything except the title: `[T0] #401 astra-core  @alice`. Line 2 is the title, flush-left, truncated with `…`.

**Alternatives rejected:**
- *Author + title on line 2* (e.g. `@alice  fix: …`): the title's start column jitters with author-name length — the raggedness we're fixing.
- *Three-line rows* (repo / author / title): full separation but burns ~33% of vertical queue density for the same title width a 2-line row already provides.
- *Keep the reason chip*: the 40-column budget cannot hold title + chip + author; the chip starves the title to ~6-13 usable characters.

### 2. Drop the reason chip from the list
The tier badge already encodes the reason class (T0 = bottleneck, T1 = direct/hot/re-review, T2 = touched files — calculator.py), and the overview shows the full rationale on selection. Reason chips are assigned in `_populate_list` from `score.reasons[0]` — that branch is removed.

### 3. Ellipsis truncation: nominal constant, clamped to the real width
`ROW_WIDTH = 36` is the *nominal* per-row budget, derived empirically as 42 (panel) − 1 (pane border) − 4 (the OptionList's own border + horizontal padding) − 1 safety column. `_truncate(text, width)` returns `text` unchanged when it fits, otherwise `text[: width - 1] + "…"`.

The nominal constant alone is not enough: when the terminal is too narrow for the fixed panes (or after a live resize), the compositor paints the list narrower than its CSS width, and OptionList still reports its nominal size — rows then wrap mid-line and OptionList crops the overflow, eating authors and titles. So the effective width is clamped at populate time: `min(ROW_WIDTH, available)` where `available` is derived from the pane's laid-out content region when it is meaningful, otherwise from the current screen width (leaving the fixed right panes their room), with a `MIN_ROW_WIDTH = 8` floor.

Rows are re-measured on window changes via an app-level resize hook (`GitkeeperApp.on_resize`) plus the widget's own `on_resize`; re-population preserves the highlighted selection. This keeps the constant for the normal case while degrading gracefully (titles shorten, authors never leave line 1, nothing wraps) at any window width.

**Alternatives rejected:** computing the budget purely from `option_list.content_size.width` at populate time — it reports the nominal CSS width even when the compositor has painted the list narrower. A resize-agnostic constant only — breaks under narrow windows/resizes. Re-measuring via the widget's `on_resize` alone — the pane's own region never changes in the fixed-width layout, so the event doesn't fire; the app-level `Resize` message carries the authoritative new width.

### 4. Guard pathological names so rows never wrap
Metadata in line 1 is allocated against a per-row budget: the repository is ellipsis-truncated first so the author stays visible; if even a minimal handler is too long (e.g. `@teeguan-super-long-handle-name`), the author is tail-ellipsised instead and the repo yields. The tier badge and PR number always remain. In practice these are ceiling guards, not active paths.

### 5. Author styling
Author rendered dim (`style="dim"`), number stays bold-cyan hyperlinked, tier badge keeps its tier color, repo keeps magenta — matching the existing overview color vocabulary so the author reads as secondary metadata.

## Risks / Trade-offs

- **Long real-world handles + long repos can squeeze the repo hard** on line 1 → the repo truncates first; a pathological handle truncates with an ellipsis rather than wrapping (decision 4).
- **Loss of at-a-glance "why is this in my queue"** per row → the tier badge preserves the priority signal and the overview rationale replaces the chip on selection.
- **`ROW_WIDTH` still nominally tracks the panel and OptionList CSS** → the effective width clamps to the actual screen/pane width on every populate and resize, so drift or narrow windows degrade instead of wrapping.
- **Resize re-population timing** (app-level event fires before the new layout is computed) → the handler threads the authoritative event width through to `_populate_list`; the live-screen fallback only applies when no explicit width is available.

## Migration Plan

Pure presentation change; no data or config migration. Rollback is reverting `_populate_list`.

## Open Questions

None.