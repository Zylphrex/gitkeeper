## 1. Worker-based markdown updates

- [x] 1.1 Add an `@work(exclusive=True)` async method to `PROverviewView` (e.g. `_update_pr_markdown`) that calls `markdown_view.update(body)` and awaits the returned `AwaitComplete`
- [x] 1.2 Replace the direct `markdown_view.update(body_content)` call in `update_pr` (`overview_view.py:246`) with a call to the worker method, leaving all label/metadata updates synchronous
- [x] 1.3 Keep a reference to the running worker (e.g. `self._markdown_worker`) so subsequent selections supersede it via exclusivity

## 2. Redundant re-render guards

- [x] 2.1 Track the last rendered body string on `PROverviewView` and skip scheduling the worker when the incoming body is unchanged
- [x] 2.2 Skip the overview update in `GitkeeperApp._select_pr` (`app.py:160`) when the selected PR is the already-current one (same PR identity)
- [x] 2.3 Debounce body renders: debut via `set_timer(MARKDOWN_DEBOUNCE_MS)` with `Timer.reset()` on each new request, rendering the *latest* pending body only after navigation quietens (so a held-key burst produces zero renders)
- [x] 2.4 Guard redundant diff loads in `_select_pr`: track `_diff_loading_key` and skip `show_loading`/re-dispatch for a PR whose fetch is already in flight; clear the key when the diff lands or errors

## 3. Regression test

- [x] 3.1 Add a test in `tests/test_ui.py` that spams `pilot.press("j")`/`("k")` across PRs with multi-section markdown bodies, then exits the `run_test` context
- [x] 3.2 Assert the run completes without emitting `exception was never retrieved` / unhandled asyncio `CancelledError` warnings — driven in a subprocess through the real `App.run()`/`asyncio.run` shutdown path, with a slowed `Markdown.update`, bursts, and then `q` (verified to fail on pre-fix code)
- [x] 3.3 Assert the last-previewed PR body is still rendered after the navigation burst (with a real-time `pilot.pause` so the debounce timer fires deterministically)
- [x] 3.4 Run the full test suite (`uv run pytest` / project test command) and confirm no regressions in existing overview and vim-navigation UI tests
- [x] 3.5 Harden pre-existing flake in `test_pr_list_view_and_selection`: drain the `_load_scored_prs` preserved-selection highlight event before acting on the option list (unrelated to this change; flakes intermittently on HEAD too)

## 4. Verification

- [x] 4.1 Manually drive the real TUI: rapid `j`/`k` navigation over a loaded queue, then `q`, and confirm no `_GatheringFuture` traceback in the terminal output