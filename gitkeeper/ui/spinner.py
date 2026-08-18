SPINNER_FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")
SPINNER_CADENCE = 0.08


class SpinnerMixin:
    """Drives an animated braille spinner through a single Textual interval timer."""

    _spinner_timer = None
    _spinner_frame = SPINNER_FRAMES[0]
    _spinner_frame_index = 0

    def _spinner_start(self) -> None:
        """Begin frame cycling, reusing a running timer if one already exists."""
        if self._spinner_timer is not None:
            return
        self._spinner_frame_index = 0
        self._spinner_frame = SPINNER_FRAMES[0]
        self._on_spinner_frame(self._spinner_frame)
        if getattr(self, "is_mounted", False):
            self._spinner_timer = self.set_interval(SPINNER_CADENCE, self._spinner_tick)

    def _spinner_stop(self) -> None:
        """Halt frame cycling. Safe to call when no spinner is running."""
        if self._spinner_timer is not None:
            self._spinner_timer.stop()
            self._spinner_timer = None

    def _spinner_tick(self) -> None:
        self._spinner_frame_index = (self._spinner_frame_index + 1) % len(SPINNER_FRAMES)
        self._spinner_frame = SPINNER_FRAMES[self._spinner_frame_index]
        self._on_spinner_frame(self._spinner_frame)

    def _on_spinner_frame(self, frame: str) -> None:
        """Re-render loading labels with the current frame. Override in subclasses."""

    @property
    def spinner_is_running(self) -> bool:
        return self._spinner_timer is not None