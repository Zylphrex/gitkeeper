## 1. Shared Spinner Primitive

- [x] 1.1 Create `gitkeeper/ui/spinner.py` defining `SPINNER_FRAMES` (braille cycle `⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏`), `SPINNER_CADENCE = 0.08`, and a `SpinnerMixin` with `_spinner_start()` / `_spinner_stop()` managing a single `set_interval` timer and a `_on_spinner_frame(frame)` hook
- [x] 1.2 Ensure `_spinner_start()` is idempotent (reuse running timer) and `_spinner_stop()` is safe to call when not running

## 2. Header Integration

- [x] 2.1 Have `AppHeader` inherit `SpinnerMixin` and render the live frame in `_render_status_text()` (static `⠋` replaced by the current frame)
- [x] 2.2 Start the spinner in `watch_is_loading` when `is_loading` becomes truthy and stop it when falsy (covers `set_idle`/`set_error` transitions)
- [x] 2.3 Remove the unused `LoadingIndicator` import from `gitkeeper/ui/header.py`

## 3. Diff View Integration

- [x] 3.1 Have `PRDiffView` inherit `SpinnerMixin`; `show_loading` renders the live frame in the diff header and disabled loading option, implementing `_on_spinner_frame` to re-render them
- [x] 3.2 Stop the spinner in `load_diff` and `show_error` so animation halts on success or failure

## 4. Tests and Verification

- [x] 4.1 Update `tests/test_ui.py`: confirm the initial-frame assertion (`header._render_status_text() == "⠋ Fetching PRs..."`) still holds after `set_loading`, add a frame-advance test that drives the tick handler directly (no sleeps), and assert diff-view loading starts/stop animation on `show_loading`/`load_diff`
- [x] 4.2 Run `pytest` and confirm the full suite passes