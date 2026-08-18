## Context

The overview panel (`PROverviewView` in `gitkeeper/ui/overview_view.py`) renders four `Label` widgets on a `width: 44` column. Its current layout has two structural problems: `Label` defaults to `width: auto`, so any line longer than the panel is **clipped at the edge** (never wrapped) — the PR title, the repo/author/change/CI line, and the score rationale are all silently truncated; and the two metadata containers use `Vertical`, which expands to `height: 1fr`, so each box consumes a fixed third of the column and crowds out the PR body. Nothing about the layout was validated visually: the existing UI tests assert widget state, never rendering.

See proposal.md - Why for motivation; spec deltas in specs/ define the observable behavior.

## Goals / Non-Goals

**Goals:**
- All PR metadata lines wrap at the panel edge; no information is silently clipped.
- The overview column keeps its fixed width (44) — the fix must not depend on a wider terminal.
- Show the already-fetched-but-hidden GitHub fields: created/updated dates, requested reviewers, existing review summary.
- Introduce base/head branch refs into the fetched PR data model and render them.
- Keep the change small and dependency-free.

**Non-Goals:**
- Not restyling the queue list, the diff pane, or the header.
- No new config options, no resizable/splittable panes, no mouse interaction.
- No changes to scoring behavior — the score box is reformatted, not recomputed.

## Decisions

### 1. Use bounded `width: 1fr` labels so text wraps instead of being clipped
Textual `Label`/`Static` wrap their content at the container edge **only** when their resolved width is a finite value (`1fr`), not the default `width: auto`. Verified by rendering the widget: with `auto`, a long line is cut at the panel edge; with `1fr`, it flows onto full wrapped lines inside the panel.

**Alternative considered:** manually wrapping strings with `textwrap` at a fixed column count before calling `Label.update()`. Rejected — it duplicates Textual's own wrap logic, breaks when the panel width changes, and mangles existing word-boundary rendering.

### 2. Swap the meta/score containers from `Vertical` to `VerticalGroup`
`Vertical` is `height: 1fr` (the two boxes claimed equal fixed thirds of the column, leaving dead space). `VerticalGroup` is `height: auto` — boxes hug their content and the `VerticalScroll` body (also `1fr`) takes the rest. Applied to both `#pr-meta-box` and `#pr-score-box`.

**Alternative considered:** Grid layout with a key/value column. More visual structure, but value wrapping in a narrow column inside a 44-wide panel is worse than full-width wrapping rows.

### 3. Enrich the metadata label with optional stacked rows
Meta keeps the single `Label` id, and `update_pr()` composes rows joined by `\n`, each row falling back when a piece is missing:

- `Repo: … · Author: @…`
- `base: … ← head: …` *(only when both provided)*
- `CI: <colored> · Δ: +add / -del · files: n`
- `Created: 2026-08-01 · Updated: 1h ago` *(relative optional)*
- `Reviewers: a, b, c +N more` *(capped at three, only when reviewers exist)*
- `Reviews: 2 ✓ · 1 ✗` *(compact per-state count from the already-fetched `reviews` list)*

The title line keeps `#N` + title + a `[DRAFT]` badge when `is_draft`, wrapping to as many rows as the title needs. Everything hangs off one `width: 1fr` label, so the stack wraps as a unit.

### 4. Small formatting helpers, no new dependencies
Two pure functions defined alongside the widget (testable in isolation, no new deps in `gitkeeper/ui/`):
- CI state → rich color: SUCCESS=`green`, FAILURE/ERROR=`red`, PENDING=`yellow`, otherwise `dim`.
- ISO-8601 timestamp → compact relative form (`Updated: 1h ago`, `3d ago`, `2w ago`); parse defensively with try/except.

### 5. Extend the GitHub query and data model (non-breaking)
- `REVIEW_REQUESTS_QUERY` PR fragment adds `baseRefName` and `headRefName` (both standard PullRequest fields).
- `PullRequestData` gains two optional string fields (`base_ref`, `head_ref`, defaulting to `None`).
- `fetch_pending_review_requests` parses them (`None` when absent).
- Existing callers/tests that construct `PullRequestData` positionally stay compatible (new fields are trailing and optional).

## Risks / Trade-offs

- **Long unbreakable tokens** (a repo slug or URL >40 chars with no spaces) cannot be wrapped mid-token and will overflow at the edge. → Set `overflow-x: ellipsis` on the meta label so the worst case shows `…` rather than a silent cut.
- **Width-dependent rendering tests** (snapshots) can drift across terminals and fonts. → Use `pytest-textual-snapshot` with an explicit pinned app size (e.g. 100x30) and keep classic state-based assertions as well.
- **Relative time rendering** introduces time-dependence if a golden snapshot includes it. → Keep the clock stable in tests (mock/frozen now) and assert the rendered string textually.
- **Added GraphQL fields** may make the existing mocked client fixtures drift from the real API shape. → Update the fixture JSON in the same landing and add a fixture comment noting the two new keys.
- **Hugging the meta box with long titles** pushes the PR body below the fold faster on short terminals → acceptable; the body scrolls.