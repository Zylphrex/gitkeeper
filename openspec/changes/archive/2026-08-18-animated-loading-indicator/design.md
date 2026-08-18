## Context

The TUI currently renders loading feedback with a single hardcoded braille glyph (`⠋`) that never animates. This appears in two places: the `AppHeader` active-status message (`gitkeeper/ui/header.py`, `_render_status_text`) and the diff view's `show_loading` state (`gitkeeper/ui/diff_view.py`). `header.py` imports Textual's `LoadingIndicator` but never uses it; proved at runtime (Textual 8.2.8) that widget is genuinely animated (pulsing dots at ~60fps) but defaults to `width: 100%; height: 100%` — a chunky full-viewport block that does not fit a 1-line header without CSS surgery, and its dot glyphs change the visual language. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- Animate the header's active-status spinner and the diff view's loading spinner using one shared mechanism.
- Keep the existing layout/compose untouched — no restructuring of the header row or diff options.
- Stop animation cleanly when the background operation ends (idle, diff loaded, or error).

**Non-Goals:**
- No changes to the bottom status bar (stays plain text).
- No introduction of Textual's `LoadingIndicator` widget.
- No changes to fetch/scoring logic, worker scheduling, or refresh lifecycle.

## Decisions

### Decision 1: Lightweight frame-cycling mixin over Textual's `LoadingIndicator`
- **Choice**: A new `gitkeeper/ui/spinner.py` module defining `SPINNER_FRAMES` (braille cycle: `⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏`) and a `SpinnerMixin` that drives frame cycling with `self.set_interval`.
- **Rationale**: A mixin plugs into both widgets with no layout change — each widget keeps composing a single status `Label` and simply renders the live frame. `set_interval` is a Textual-native timer primitive; starting/stopping is straightforward. The already-imported `LoadingIndicator` was rejected because its full-viewport default sizing and dot glyphs require CSS restructuring of the 1-line header and change the established braille visual style.
- **Alternatives Considered**: (a) Textual `LoadingIndicator` widget — see above; (b) a standalone `AnimatedSpinner(Label)` widget composed next to the status text — works but forces compose/CSS changes in both header and diff view, which the mixin avoids.

### Decision 2: Mixin lifecycle contract
- **Choice**: `SpinnerMixin` exposes `_spinner_start()` and `_spinner_stop()` that manage a single timer instance. Widgets call `_spinner_start()` when entering a loading state and `_spinner_stop()` when leaving it. Each tick invokes a `_on_spinner_frame(frame: str)` hook the widget implements to re-render its labels.
- **Rationale**: Keeps cycle bookkeeping in one place while letting each widget decide what to re-render. Guards against double-start by reusing an existing timer.
- **Call sites**:
  - `AppHeader.watch_is_loading` — start when `is_loading` becomes truthy, stop when falsy (covers idle and error transitions via existing `set_idle`/`set_error`).
  - `PRDiffView.show_loading` — start; `PRDiffView.load_diff` and `show_error` — stop.
- **Alternatives Considered**: Reactive `spinner_frame` on the header re-rendered through Textual's watcher at ~12Hz — rejected as unnecessary machinery and harder to share with the diff view.

### Decision 3: Initial frame is `⠋`
- **Choice**: The cycle starts on `⠋`, the first frame and the current static glyph.
- **Rationale**: With no timer tick having fired yet, `_render_status_text()` after `set_loading()` still yields `"⠋ <status>"`, so the existing assertion in `tests/test_ui.py` (`header._render_status_text() == "⠋ Fetching PRs..."`) keeps passing. Tests that assert frame advancement add ticking rather than rewriting it.
- **Alternatives Considered**: Starting on a different frame, which would churn existing assertions.

### Decision 4: Fixed shared cadence
- **Choice**: A single `SPINNER_CADENCE = 0.08` seconds per frame, shared by header and diff view (each owns its own timer, same period).
- **Rationale**: One source of truth for speed keeps the two spinners visually consistent; ~12 fps is a smooth, calm braille spinner.

## Risks / Trade-offs

- **[Risk] Timer leak / animation left running** → If `_spinner_stop()` is missed, the interval keeps re-rendering the header or diff even when idle.
  - *Mitigation*: Stop is driven by the same transitions already wired (idle/error set `is_loading = False`; diff `load_diff`/`show_error` call `_spinner_stop`). Mixin reuses one timer and stops it on the False branch; `_spinner_start` ignores a second call while running.
- **[Risk] Noise from re-render churn** → Updating a `Label.update()` at ~12 Hz is cheap, but on very small terminals combined with reactive re-renders it could add layout work.
  - *Mitigation*: Frame is stored as a plain attribute updated directly in the tick callback, bypassing Textual's reactive watcher path; accepted as low risk given the header is a single 1-line row.
- **[Risk] Test fragility on timing** → Tests that assert a moving frame depend on the timer having ticked.
  - *Mitigation*: Keep the initial-frame assertion (Decision 3) tick-free; add frame-advance assertions that tick the timer explicitly (e.g., invoke the internal tick handler directly) rather than sleeping.

## Migration Plan

No deployment or rollback concerns — this is an in-repo UI change. The old static-`⠋` rendering and the unused `LoadingIndicator` import are removed in the same change; revert by reverting the commit.

## Open Questions

None — cadence, initial frame, lifecycle hooks, and scope are settled.