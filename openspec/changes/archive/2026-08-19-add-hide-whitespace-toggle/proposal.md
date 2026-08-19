## Why

Large diffs are often dominated by whitespace-only churn (trailing whitespace, whole-file reindents), which buries the real content changes a reviewer is trying to see. GitHub's web Files view offers a "hide whitespace" toggle for exactly this reason, and git supports the same comparison natively via `git diff -w` (`--ignore-all-space`). The GitKeeper diff viewer has no equivalent, so reviewers must read through noise or leave diffs unreadable. GitHub's REST diff endpoint ignores `?w=1` (verified empirically — the param returns byte-identical output), so the only reliable way to deliver this is to re-derive the diff client-side.

## What Changes

- Add a client-side "hide whitespace" mode to the in-TUI diff viewer that behaves like `git diff -w`: lines that differ only in whitespace SHALL be re-classified as unchanged context instead of appearing as added/deleted change pairs, and hunks that collapse to nothing SHALL be dropped.
- Bind the `w` key to toggle the mode on and off; the mode is a view preference, not a config setting, and toggling re-renders the currently displayed PR's diff in memory without refetching from GitHub.
- Show a visible indicator in the diff pane header and/or footer when the mode is active so the reviewer knows whitespace is hidden.
- Changes that are not whitespace-only SHALL render exactly as they do today; only whitespace-only differences are affected.

## Capabilities

### New Capabilities
<!-- none: this extends the existing diff viewer behavior -->

### Modified Capabilities
- `tui-review-client`: Extend the **In-TUI Diff Viewer** requirement so reviewers can toggle a whitespace-hiding mode with `w` that re-derives the diff on a whitespace-insensitive comparison (like `git diff -w`), affecting only whitespace-only differences while leaving other change lines rendered unchanged.

## Impact

- `gitkeeper/diff/parser.py` (or a new sibling module): adds a pure client-side whitespace-insensitive re-derivation that converts whitespace-only change pairs into context lines and drops collapsed hunks.
- `gitkeeper/ui/diff_view.py`: `PRDiffView` gains the toggle state, a re-derivation hook applied between parsing and rendering, and a visible active-state indicator.
- `gitkeeper/ui/app.py`: adds the `w` key binding and wires the action to the diff view.
- Tests: new parser-level unit tests proving whitespace-ignoring behavior matches `git diff -w` on craft decisions, plus UI tests for the toggle key, indicator, and re-render.
- No network layer or caching changes; the cached diff text is re-derived on toggle.