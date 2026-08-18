## Context

See `proposal.md` for motivation. The TUI (`gitkeeper/ui/app.py`) renders ranked PRs in a left `PRListView` (`OptionList`) with the overview (`PROverviewView`) on the right, and the PR's GitHub URL is already available on `PullRequestData.pr.url` from GraphQL. The archived `link-pr-in-terminal-table` change defined OSC 8 hyperlinks for the now-removed non-TUI table; that mechanism and Rich markup carry over here. Textual's `App.open_url` delegates to `webbrowser.open` on the Linux/macOS terminal driver, which is what the `o` binding needs.

## Goals / Non-Goals

**Goals:**
- Make the PR openable from the TUI by (a) rendering PR-number hyperlinks and (b) an `o` keybinding that opens the current PR in the default browser.
- Reuse `pr.url` with a graceful fallback when it is missing.
- Keep the change additive: no new dependencies, no change to existing keys, selection, or focus behavior.

**Non-Goals:**
- Reviving the removed non-TUI `queue`/`list` table (the archived `link-pr-in-terminal-table` change is superseded by the TUI-only CLI; no table work here).
- A dedicated URL column or URL display in the TUI — the hyperlink affordance and `o` cover it without layout cost.
- Opening files/lines in the diff view in the browser (future possibility, out of scope).

## Decisions

### 1. Link the PR number via Rich hyperlink markup
- **Choice**: In `PROverviewView.update_pr` (`overview_view.py:204`), wrap the number as `[link={pr.url}]#{pr.number}[/link]` inside the existing title markup. In `PRListView._populate_list` (`list_view.py:91`), render the number via `Text.append(f"#{number} ", style=f"bold cyan link {url}")` (Rich's `link` text style) when a URL exists.
- **Rationale**: Both are OSC 8 terminal hyperlinks — hovering shows the URL and the terminal opens it on click/meta-click, consistent with the mechanism the queue table used and with zero layout impact. Rich markup degrades to plain text in terminals without OSC 8.
- **Alternative considered**: A keybinding only, or a visible URL column. Rejected: the `o` key works everywhere, and a URL column wastes the narrow panels; markup gives the hover/click affordance the user asked for.

### 2. `o` binding opens the current PR in the browser
- **Choice**: Add `Binding("o", "open_browser", "Open in Browser")` to `GitkeeperApp.BINDINGS` and implement `action_open_browser`:
  - if a modal is open (`_guard_vim_action()`), return (no-op), matching other global key handling;
  - if `self.current_scored_pr` is None → status "No PR selected.";
  - if `pr.url` is falsy → status "No URL available for this PR.";
  - else `self.app.open_url(pr.url)` and reflect it in the status bar.
- **Rationale**: `o` is unbound today; a single global action on the always-present current selection is the smallest, most predictable surface, and works regardless of which pane has focus. `App.open_url` reuses Textual's own browser plumbing (`webbrowser.open`) rather than adding a bespoke import.
- **Alternative considered**: Scoping `o` to the PR-list zone only. Rejected: the current PR is meaningful from any pane, and a from-anywhere key matches expectations for "open what I'm looking at".

### 3. URL-aware fallback
- **Choice**: Only emit a hyperlink when `pr.url` is present; otherwise render the plain `#<number>`. Mirrors the table behavior and avoids pointing a link at a broken/empty string.
- **Rationale**: `PullRequestData.url` is generally populated, but the fallback keeps rendering and `o` correct when it is not.

## Risks / Trade-offs

- **[Risk] Terminal emulator lacks OSC 8 hyperlink support** → **Mitigation**: Rich renders plain `#<number>` in such terminals; the `o` keybinding remains the reliable path to open the PR.
- **[Risk] Clicking a list-row hyperlink selects the option instead of opening it** → **Mitigation**: `OptionList` click handling selects the row (existing behavior); the overview header label is the primary click-to-open surface and remains unambiguously clickable. `o` works from the list regardless.
- **[Risk] `o` fires while a modal or input is focused** → **Mitigation**: guard with `_guard_vim_action()` for modals; a focused `Input` consumes keys so search typing is unaffected.
- **[Risk] No URL available** → **Mitigation**: `o` reports it in the status bar and renders no hyperlink, so nothing attempts a bogus open.
