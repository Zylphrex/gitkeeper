## Context

`PROverviewView.update_pr` (`gitkeeper/ui/overview_view.py:178`) is a synchronous method. Its last line calls `markdown_view.update(body_content)`, which returns `textual.await_complete.AwaitComplete` wrapping `asyncio.gather(await_update())`. `Textual.Markdown` serializes renders through an internal `RLock` (`textual/widgets/_markdown.py:1402`).

Because the returned `AwaitComplete` is dropped, nothing ever awaits the `_GatheringFuture`. Every list highlight posts a `PRSelected` message which re-enters `update_pr`; each call queues another `await_update` coroutine behind the lock. On quit, the app's `asyncio.run` shutdown calls `_cancel_all_tasks`, cancelling tasks still blocked on `lock.acquire()`; the un-awaited gather future keeps the raised `CancelledError` as its "never retrieved" exception, producing the reported warning.

See `proposal.md` — Why for motivation, `specs/terminal-interface/spec.md` for requirements.

## Goals / Non-Goals

**Goals:**
- Every `Markdown.update()` is eventually awaited or cancelled *and consumed* by the framework, so no `_GatheringFuture ... was never retrieved` warning can surface.
- Preview renders coalesce: during a navigation burst the body preview is rendered at most once, for the latest selection.
- Avoid re-rendering when the selected PR or its body text are unchanged.
- Keep rapid navigation responsive: the event loop must not be saturated with markdown mount work on every highlight.

**Non-Goals:**
- Imposing a strict settle threshold on the diff fetch; loading state is just no longer reset redundantly for the same in-flight PR.
- Fixing Textual's `Markdown` widget internally (dependency change).
- Serializing label/metadata updates; those stay fast and synchronous.

## Decisions

### 1. Move the markdown update into an exclusive async worker

`PROverviewView` gains an `@work(exclusive=True)` async worker method (a coroutine, so no `thread=True`) that awaits the `AwaitComplete` returned by `Markdown.update()`. `update_pr` schedules the worker with the body string instead of calling `Markdown.update()` directly.

- `exclusive=True` coalesces superseded renders: a newer render cancels the prior worker, which cancels the `AwaitComplete`'s gather future, which cancels the queued `await_update()` coroutine. Textual's `Worker` records the cancellation (consuming it), so nothing is "never retrieved."
- Awaiting inside the worker is required — if the worker is left as a bare call it reintroduces a fire-and-forget future.
- The worker must run on the app's event loop (`thread=True` would run widget APIs from a foreign thread); `Markdown.update()` already hops the parse into an executor internally.

Alternative considered: manually keeping the previous `AwaitComplete` and calling `.cancel()`/reading `.exception` on replace. Correct but reinvents worker cancellation semantics and spreads lifecycle code through the view.

### 2. Debounce body renders

`_schedule_markdown` no longer renders inline. It records the pending body, then arms a `set_timer(MARKDOWN_DEBOUNCE_MS, ...)`; each new request while a timer is armed calls `Timer.reset()`. When the timer fires, the latest pending body is handed to the exclusive worker (decision 1) and `_rendered_body` is updated only after the render actually completes.

- A burst of highlights during navigation therefore produces **zero** renders; one render starts after the user stops for `MARKDOWN_DEBOUNCE_MS` (0.12s). Measured: per-key latency drops from ~120ms to ~94ms, and — more importantly for a real terminal — the event loop is never saturated with per-key mount/layout work.
- The debounce window is short enough that the preview tracks the cursor after you stop scrolling (slight trailing lag is intentional; user-confirmed behavior).
- On shutdown with a pending timer, Textual cancels timers (`Timer._stop_all`), so no abandoned render task exists; with a render in flight, the exclusive worker consumes the cancellation.

Alternative considered: a non-cancelling drain-loop worker that renders every distinct body but never more than one in flight. Removes cancel/restart churn but still renders each intermediate body during a held key, so it does not fix the perceived lag.

### 3. Guard re-renders in `update_pr`

Track the last rendered body string (`self._rendered_body`). If the incoming body equals the current one, skip the debounce entirely. Also skip the overview update when `_load_scored_prs` re-selects the already-current PR — handled in the app via an identity check in `_select_pr`.

This avoids repeated highlight of the same PR and queue refreshes re-emitting the current body. It is complementary to decisions 1 and 2.

### 4. Guard redundant diff-loading resets

`_select_pr` tracked `self._diff_loading_key`. When re-selecting a PR whose diff fetch is already in flight, skip `show_loading`/`_fetch_diff_for_pr` re-dispatch (previously every highlight reset the diff pane and kept the spinner/OptionList churning). The key is cleared when the diff lands (`_display_cached_diff`) or fails (`_display_diff_error`).

### 5. Regression test drives the real shutdown path

The decisive regression test runs the real app in a subprocess under `App.run()` (which ends in `asyncio.run`, the exact loop-closure that originally surfaced the warning): a slow `Markdown.update` (patched in the driver), navigation bursts, then `q`. It asserts stderr contains no `never retrieved` / `_GatheringFuture`. Verified to fail against the pre-fix code and pass with the fix.

Alternative considered: `App.run_test` + `pilot` only — `run_test` drains to idle before teardown, so it never reproduces the original warning.

## Risks / Trade-offs

- [Cancelled worker skips the latest-render flag] A superseded worker may be cancelled before it sets internal state. → `_rendered_body` is only set after a render completes; a cancelled render leaves it stale but the next selection schedules again (the guard only skips identical bodies).

- [Debounced preview lags the cursor] → Intentional: `MARKDOWN_DEBOUNCE_MS = 0.12` is under human perception thresholds for a preview pane, and it is what makes bursts cheap.

- [Timer fires after unmount] → Textual stops timers on shutdown; `_render_pending_markdown` also guards pending/rendered equality.

- [Run on the event loop] An async worker runs on the app's loop; a slow markdown parse temporarily occupies the loop between the parse executor's result and the mount. → The parse itself is already async via `run_in_executor`, so only the mount work runs on the loop; the debounce prevents a cascade of them.

- [Placeholder body `_No description provided._` now also coalesces] → intentional, same string yields reduced work.

- [Behavior in tests] → The regression test asserts on absence of the warning via the real `asyncio.run` shutdown; the rendered-body test adds a real-time `pilot.pause` so the debounce timer fires deterministically.

## Open Questions

None.