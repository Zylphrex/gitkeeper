## Context

See proposal.md — Why. The diff reaches the screen through a strict pipeline: GitHub REST diff text → `cached_diffs` on the app (gitkeeper/ui/app.py:114) → `UnifiedDiffParser.parse(text)` → `List[FileDiff]` held by `PRDiffView` → `_render_file_list` builds the tree and `DiffViewer.set_file_diff` renders the current file's `hunks`.

Two facts constrain the design:

1. **The server cannot do it.** `GET /pulls/{n}?w=1` with the `application/vnd.github.v3.diff` media type returns byte-identical output, even on a PR whose only change is a trailing whitespace cleanup (verified empirically). GitKeeper's diff source cannot be asked for a whitespace-hidden diff.
2. **The toggle must be a re-derivation, not a display filter.** `git diff -w` removes whitespace-only `-`/`+` pairs from the *changed* region and turns them into **common context lines**. That is reconstructing structure (which rows are changes) — impossible at the `OptionList` row level, which only knows the already-rendered rows.

## Goals / Non-Goals

**Goals:**
- Re-derive the parsed `FileDiff` structures so whitespace-only changes vanish the way `git diff -w` renders them (pairs become context, empty hunks drop) — pure, testable, no network.
- Make it a per-session view toggle bound to `w`, with a visible active indicator.
- Preserve exact rendering/numbering of non-whitespace changes.

**Non-Goals:**
- No server-side whitespace handling, no config key, no persistence across a restart.
- No change to how comments, threads, or submissions target lines.
- No attempt to byte-match `git diff -w` hunk headers exactly (see Risks) — visible line content and line numbers are the contract.

## Decisions

### 1. Client-side re-derivation in a pure function (`gitkeeper/diff/whitespace.py`)

- **Decision**: Add `hide_whitespace(file_diffs: List[FileDiff]) -> List[FileDiff]` in a new pure module (or near the dataclasses in `parser.py`). It consumes the already-parsed hunks and returns a new list with whitespace-only changes collapsed. It never touches the network or the render layer, so it is unit-testable in isolation.
- **Rationale**: Server can't do it (see Context); a render-layer filter can't reconstruct line structure. The parser output is the last structured representation before the UI, so that's where the re-derivation goes.
- **Alternative considered**: calling `git diff -w` locally — rejected because the diff comes from the GitHub API, not a local clone, and local refs may be missing.

### 2. Per-hunk whitespace-insensitive alignment (LCS over old/new sequences)

- **Decision**: Within each hunk, build two sequences — `old_lines` (context rows + `-` rows) and `new_lines` (context rows + `+` rows) — and run a longest-common-subsequence alignment where equality means *equal after removing all whitespace* (`re.sub(r"\s+", "", a) == re.sub(r"\s+", "", b)`, git's `--ignore-all-space`). Emit:
  - aligned pair, ws-equal → one **context** `DiffLine` carrying both the old and new line numbers (content from the new side);
  - aligned pair, not ws-equal → unchanged `-`/`+` pair;
  - unpaired old line → `-`; unpaired new line → `+`.
- **Rationale**: Handles interleaved hunks (e.g. a ws-only line nested between real changes) far better than adjacent-pair pattern-matching, which misaligns whenever deletions and additions interleave. Hunks are bounded (tens of lines), so `O(n·m)` is fine.
- **Alternative rejected**: Scan for adjacent `- old + new` pairs and drop them. Fails on interleaved hunks and on hunks where counts deny.
- Line numbers are **not re-invented**: each emitted row keeps the side's absolute line numbers that the original parser already assigned (they are real file positions). Only ws-only pairs merge into one context row; nothing after them shifts.

### 3. Collapsed and fully-whitespace hunks/files

- **Decision**: When a hunk's every change row collapses to context, drop the hunk (its header row too, via `all_lines`). When a `FileDiff`'s hunks are all dropped, keep the file in the changed-files tree but render its diff pane with an explicit "No visible changes — whitespace only" note.
- **Rationale**: Dropping the hunk is required (`-w` removes empty change blocks). Dropping the whole file row would silently remove a changed file from the tree — worse than keeping it with a clear note, because the file *did* change (whitespace).
- **Alternative rejected**: keep a fully-collapsed file's file honest but list it without a note — reviewer can't tell why the pane is blank.

### 4. State ownership: PRDiffView holds the toggle; the app binds `w`

- **Decision**: `GitkeeperApp` gains `Binding("w", "hide_whitespace", "Hide Whitespace")` calling `PRDiffView.hide_whitespace_active = not ...`. The view re-renders from the last parsed diff in memory — no refetch, no cache-key changes.
- **Decision**: The re-derivation composes with the existing file-filter: toggling `hide_whitespace_active` clears any active `/`-file filter and re-renders using `self.file_diffs` re-derived from the authoritative parsed list (`self._parsed_diffs`). Default is off (`hide_whitespace_active = False`).
- **Rationale**: The diff pane is `PRDiffView`-owned (proposal). Keeping raw parsed list authoritative avoids re-parse and makes the toggle cheap; composing by resetting the file list filter matches how search filtering already rebuilds rows.
- **Alternative considered**: an app-level bool passed through every render — rejected, the view already holds file state.

### 5. Visible indicator

- **Decision**: When active, the `DiffViewer` header (`#diff-header`) appends a marker (e.g. ` · whitespace hidden`) and the Footer binding entry already shows `w — Hide Whitespace`. 
- **Rationale**: The reviewer must be able to tell they're on a filtered diff; the header is already visible in the diff pane and the footer advertises the key.

### 6. Test oracle: compare against `git diff -w`

- **Decision**: Crafted diff fixtures (trailing-space hunks, whole-file reindent, interleaved ws+hwn+real-change) feed `hide_whitespace` and the assertion compares the emitted rows — prefixes and line numbers — to the output git prints when the same before/after content is diffed with `git diff -w` (via the repo's existing `git` CLI in tests, or captured golden output).

## Risks / Trade-offs

- **[Risk] Alignment differs from git's own `-w` on degenerate hunks (e.g. reordered + renamed blocks)** → LCS produces a valid ws-insensitive alignment, but may not match xdiff's choice exactly (specific hunk boundaries and counts). **Mitigation**: keep visible-row behavior exact (`context` vs changed) and only ever approximate inner hunk boundaries, covered by the oracle tests; document that identical hunk headers byte-level not guaranteed.
- **[Risk] Toggle resets an in-progress file filter and scroll position** → Filtering conserv reply clears the current filter, per Decision 4-f. **Mitigation**: re-render is in memory and fast; acceptable and consistent with existing search-filter semantics. Scroll position is not part of the specs' contract for this toggle.
- **[Risk] `O(n·m)` per hunk on a large reindent hunk** → One hunk is bounded by the diff's own hunking and `git diff` without `-w` on a whole-file reindent a few hundred lines; the `n·m` alignment still runs in milliseconds per hunk in the toggle path. **Mitigation**: if sluggish in practice, cap alignment to the diff hunk size (already bounded) or memoize equality.
- **[Risk] The comment/thread line mapping wobbles on collapsed pairs** → ws-only rows become context holding both numbers, so `_line_target` behavior is preserved for targets that remain renderable; a thread pinned to a folded row simply isn't displayed (existing "unmatched thread is not rendered" rule). **Mitigation**: no new mapping logic needed; add one test asserting folded-row numbers stay reportable.

## Migration Plan

No deployment or rollback steps: session-scoped view state, no stored data, no API changes. Default off means existing behavior is unchanged until the reviewer presses `w`.