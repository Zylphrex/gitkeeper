from datetime import datetime
from typing import Optional
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, LoadingIndicator


class AppHeader(Widget):
    """Custom application header displaying brand title, active background status, and refresh timestamp."""

    DEFAULT_CSS = """
    AppHeader {
        dock: top;
        height: 1;
        background: $panel;
        color: $text;
        padding: 0 1;
    }

    #app-header-container {
        width: 1fr;
        height: 1;
    }

    #header-title {
        text-style: bold;
        color: $accent;
        width: auto;
        margin-right: 2;
    }

    #header-status {
        width: 1fr;
        color: $text-muted;
    }

    #header-timestamp {
        width: auto;
        color: $text-muted;
        text-align: right;
    }
    """

    status_text: reactive[str] = reactive("Ready")
    last_refreshed_at: reactive[Optional[datetime]] = reactive(None)
    is_loading: reactive[bool] = reactive(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        with Horizontal(id="app-header-container"):
            yield Label("gitkeeper", id="header-title")
            yield Label(self._render_status_text(), id="header-status")
            yield Label(self._render_timestamp_text(), id="header-timestamp")

    def _render_status_text(self) -> str:
        if self.is_loading:
            return f"⠋ {self.status_text}"
        return self.status_text

    def _render_timestamp_text(self) -> str:
        if self.last_refreshed_at:
            return f"Last refreshed: {self.last_refreshed_at.strftime('%H:%M:%S')}"
        return "Last refreshed: Never"

    def watch_status_text(self, new_val: str) -> None:
        try:
            status_label = self.query_one("#header-status", Label)
            status_label.update(self._render_status_text())
        except Exception:
            pass

    def watch_is_loading(self, new_val: bool) -> None:
        try:
            status_label = self.query_one("#header-status", Label)
            status_label.update(self._render_status_text())
        except Exception:
            pass

    def watch_last_refreshed_at(self, new_val: Optional[datetime]) -> None:
        try:
            ts_label = self.query_one("#header-timestamp", Label)
            ts_label.update(self._render_timestamp_text())
        except Exception:
            pass

    def set_loading(self, status: str) -> None:
        """Set the header into active loading state with a status description."""
        self.is_loading = True
        self.status_text = status

    def set_idle(self, status: str = "Ready", refreshed_at: Optional[datetime] = None) -> None:
        """Set the header into idle state and optionally update last refreshed timestamp."""
        self.is_loading = False
        self.status_text = status
        if refreshed_at is not None:
            self.last_refreshed_at = refreshed_at

    def set_error(self, message: str) -> None:
        """Set the header into error display state."""
        self.is_loading = False
        self.status_text = f"⚠ {message}"
