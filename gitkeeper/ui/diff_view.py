from typing import Dict, List, Optional
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, ListView, ListItem, OptionList, Static
from textual.widgets.option_list import Option

from gitkeeper.diff.parser import DiffLine, FileDiff, UnifiedDiffParser
from gitkeeper.github.client import DraftReviewComment, ReviewThread
from gitkeeper.ui.filestree import TreeHeader, TreeLeaf, build_file_tree
from gitkeeper.ui.modals import InlineCommentModal
from gitkeeper.ui.spinner import SPINNER_FRAMES, SpinnerMixin


def _change_badge(file_diff: FileDiff) -> str:
    if file_diff.is_new:
        return "[ADD]"
    if file_diff.is_deleted:
        return "[DEL]"
    if file_diff.is_renamed:
        return "[REN]"
    return "[MOD]"


def _line_target_no(line: DiffLine) -> Optional[int]:
    """The line number a diff line maps to for comment targeting."""
    return line.new_line_no if line.new_line_no is not None else line.old_line_no


class DiffViewer(Widget):
    """Renders syntax and line-number formatted diff lines for a single file."""

    DEFAULT_CSS = """
    DiffViewer {
        height: 1fr;
        background: $background;
        border: solid $accent;
    }

    #diff-header {
        background: $panel;
        padding: 0 1;
        text-style: bold;
        dock: top;
        height: 1;
    }

    #diff-options {
        height: 1fr;
    }
    """

    class LineCommentRequested(Message):
        def __init__(self, file_path: str, line_no: int):
            super().__init__()
            self.file_path = file_path
            self.line_no = line_no

    file_diff: reactive[Optional[FileDiff]] = reactive(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.draft_comments: Dict[str, List[DraftReviewComment]] = {}
        self.comments_by_line: Dict[int, List[str]] = {}
        self.existing_by_line: Dict[int, List[ThreadComment]] = {}
        self._rendered_lines: List[DiffLine] = []
        self._loading_header_text: Optional[str] = None
        self._loading_option_text: str = ""

    def compose(self) -> ComposeResult:
        yield Label("No file selected", id="diff-header")
        yield OptionList(id="diff-options")

    def show_loading(self, pr_identifier: str = "") -> None:
        """Display a loading state in the diff pane."""
        header = self.query_one("#diff-header", Label)
        options = self.query_one("#diff-options", OptionList)
        options.clear_options()
        self._rendered_lines = []
        self.file_diff = None

        text = f"Fetching diff for {pr_identifier}..." if pr_identifier else "Fetching diff..."
        self._loading_header_text = text
        self._loading_option_text = "Loading diff lines from GitHub..."
        header.update(f"{SPINNER_FRAMES[0]} {text}")
        loading_text = Text(f"\n  {SPINNER_FRAMES[0]} {self._loading_option_text}\n", style="dim italic")
        options.add_option(Option(loading_text, disabled=True))

    def render_loading_frame(self, frame: str) -> None:
        """Re-render the current loading state with an updated spinner frame."""
        if not self._loading_header_text:
            return
        header = self.query_one("#diff-header", Label)
        options = self.query_one("#diff-options", OptionList)
        header.update(f"{frame} {self._loading_header_text}")
        options.clear_options()
        loading_text = Text(f"\n  {frame} {self._loading_option_text}\n", style="dim italic")
        options.add_option(Option(loading_text, disabled=True))

    def show_error(self, message: str) -> None:
        """Display an error state in the diff pane."""
        header = self.query_one("#diff-header", Label)
        options = self.query_one("#diff-options", OptionList)
        options.clear_options()
        self._rendered_lines = []
        self.file_diff = None
        self._loading_header_text = None

        header.update("⚠ Diff unavailable")
        err_text = Text(f"\n  ⚠ Failed to load diff: {message}\n", style="bold red")
        options.add_option(Option(err_text, disabled=True))

    def set_file_diff(
        self,
        file_diff: Optional[FileDiff],
        existing_threads: Optional[List[ReviewThread]] = None,
        draft_comments: Optional[List[DraftReviewComment]] = None,
    ) -> None:
        self.file_diff = file_diff
        self._loading_header_text = None
        header = self.query_one("#diff-header", Label)
        options = self.query_one("#diff-options", OptionList)
        options.clear_options()
        self._rendered_lines = []
        self.comments_by_line = {}
        self.existing_by_line: Dict[int, List[ThreadComment]] = {}

        if not file_diff:
            header.update("No file selected")
            return

        header.update(f"File: {file_diff.display_path}")
        lines = file_diff.all_lines
        self._rendered_lines = lines

        if existing_threads:
            for thread in existing_threads:
                if thread.path == file_diff.display_path and thread.line is not None:
                    self.existing_by_line.setdefault(thread.line, []).extend(thread.comments)

        if draft_comments:
            for c in draft_comments:
                if c.path == file_diff.display_path:
                    self.comments_by_line.setdefault(c.line, []).append(c.body)

        for idx in range(len(lines)):
            options.add_option(Option(self._render_line(idx), id=f"line_{idx}"))

    def _render_line(self, idx: int) -> Text:
        """Render the diff line at *idx* with any existing threads and pending comments attached."""
        line = self._rendered_lines[idx]

        old_str = f"{line.old_line_no:4d}" if line.old_line_no is not None else "    "
        new_str = f"{line.new_line_no:4d}" if line.new_line_no is not None else "    "

        if line.origin == "+":
            style = "bold green"
            prefix = "+"
        elif line.origin == "-":
            style = "bold red"
            prefix = "-"
        elif line.origin == "@":
            style = "bold cyan"
            prefix = "@"
            old_str = "----"
            new_str = "----"
        else:
            style = "white"
            prefix = " "

        rich_text = Text()
        rich_text.append(f"{old_str} {new_str} │ {prefix} ", style="dim")
        rich_text.append(line.content, style=style)

        target_line = _line_target_no(line)
        if target_line and target_line in self.existing_by_line:
            for tc in self.existing_by_line[target_line]:
                rich_text.append(f"\n      💬 {tc.author}: {tc.body}", style="bold blue on #002244")
        if target_line and target_line in self.comments_by_line:
            for c_body in self.comments_by_line[target_line]:
                rich_text.append(f"\n      💬 Pending Comment: {c_body}", style="bold yellow on #332200")

        return rich_text

    def add_pending_comment(self, line_no: int, body: str) -> None:
        """Attach a pending comment to every rendered row for the line without rebuilding the list."""
        if not self.file_diff:
            return
        self.comments_by_line.setdefault(line_no, []).append(body)
        options = self.query_one("#diff-options", OptionList)
        for idx, line in enumerate(self._rendered_lines):
            if _line_target_no(line) == line_no:
                options.replace_option_prompt_at_index(idx, self._render_line(idx))

    def get_selected_line_info(self) -> Optional[tuple[str, int]]:
        if not self.file_diff:
            return None
        options = self.query_one("#diff-options", OptionList)
        idx = options.highlighted
        if idx is None or idx >= len(self._rendered_lines):
            return None
        line = self._rendered_lines[idx]
        target_line = _line_target_no(line)
        if target_line is None:
            return None
        return (self.file_diff.display_path, target_line)

    def find_matching_lines(self, query: str) -> List[int]:
        query_lower = query.lower()
        matches: List[int] = []
        for idx, line in enumerate(self._rendered_lines):
            if query_lower in line.content.lower():
                matches.append(idx)
        return matches


class PRDiffView(Widget, SpinnerMixin):
    """File tree and diff viewer container."""

    DEFAULT_CSS = """
    PRDiffView {
        height: 1fr;
    }

    #diff-container {
        height: 1fr;
    }

    #file-list-pane {
        width: 32;
        border-right: solid $primary;
        height: 1fr;
    }

    #file-list-title {
        background: $panel;
        padding: 0 1;
        text-style: bold;
        height: 1;
    }

    #file-option-list {
        height: 1fr;
        overflow-x: hidden;
    }

    #diff-viewer-pane {
        width: 1fr;
        height: 1fr;
    }
    """

    class AddCommentRequest(Message):
        def __init__(self, file_path: str, line_no: int):
            super().__init__()
            self.file_path = file_path
            self.line_no = line_no

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.file_diffs: List[FileDiff] = []
        self.draft_comments: List[DraftReviewComment] = []
        self.existing_threads: List[ReviewThread] = []
        self._file_indices: List[Optional[int]] = []

    def compose(self) -> ComposeResult:
        with Horizontal(id="diff-container"):
            with Vertical(id="file-list-pane"):
                yield Label("Changed Files", id="file-list-title")
                yield OptionList(id="file-option-list")
            with Vertical(id="diff-viewer-pane"):
                yield DiffViewer(id="diff-viewer")

    def show_loading(self, pr_identifier: str = "") -> None:
        """Set the entire diff view into a loading state."""
        self.file_diffs = []
        self.draft_comments = []
        self.existing_threads = []
        self._file_indices = []
        file_list = self.query_one("#file-option-list", OptionList)
        file_list.clear_options()
        file_list.add_option(Option(f"{SPINNER_FRAMES[0]} Loading files...", disabled=True))

        diff_viewer = self.query_one("#diff-viewer", DiffViewer)
        diff_viewer.show_loading(pr_identifier)
        self._spinner_start()

    def _on_spinner_frame(self, frame: str) -> None:
        try:
            file_list = self.query_one("#file-option-list", OptionList)
            file_list.clear_options()
            file_list.add_option(Option(f"{frame} Loading files...", disabled=True))
            diff_viewer = self.query_one("#diff-viewer", DiffViewer)
            diff_viewer.render_loading_frame(frame)
        except Exception:
            pass

    def show_error(self, message: str) -> None:
        """Set the diff view into an error state."""
        self._spinner_stop()
        self.file_diffs = []
        self.draft_comments = []
        self.existing_threads = []
        self._file_indices = []
        file_list = self.query_one("#file-option-list", OptionList)
        file_list.clear_options()
        file_list.add_option(Option("⚠ Error loading files", disabled=True))

        diff_viewer = self.query_one("#diff-viewer", DiffViewer)
        diff_viewer.show_error(message)

    def load_diff(
        self,
        diff_text: str,
        existing_threads: Optional[List[ReviewThread]] = None,
        draft_comments: Optional[List[DraftReviewComment]] = None,
    ) -> None:
        self._spinner_stop()
        self.file_diffs = UnifiedDiffParser.parse(diff_text)
        self.existing_threads = existing_threads or []
        self.draft_comments = draft_comments or []
        self._render_file_list()

    def _render_file_list(self) -> None:
        file_list = self.query_one("#file-option-list", OptionList)
        file_list.clear_options()
        self._file_indices = []

        if not self.file_diffs:
            file_list.add_option(Option("No changed files", disabled=True))
            diff_viewer = self.query_one("#diff-viewer", DiffViewer)
            diff_viewer.set_file_diff(None, self.existing_threads, self.draft_comments)
            return

        for row in build_file_tree(self.file_diffs):
            indent = "  " * row.depth
            if isinstance(row, TreeHeader):
                file_list.add_option(Option(f"{indent}{row.label}", disabled=True))
                self._file_indices.append(None)
            else:
                file_diff = self.file_diffs[row.file_index]
                file_list.add_option(
                    Option(f"{indent}{_change_badge(file_diff)} {row.label}")
                )
                self._file_indices.append(row.file_index)

        first_leaf = next(
            (i for i, file_index in enumerate(self._file_indices) if file_index is not None),
            None,
        )
        selected_file = self.file_diffs[self._file_indices[first_leaf]] if first_leaf is not None else None
        diff_viewer = self.query_one("#diff-viewer", DiffViewer)
        diff_viewer.set_file_diff(selected_file, self.existing_threads, self.draft_comments)
        if first_leaf is not None:
            file_list.highlighted = first_leaf

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        if event.option_list.id == "file-option-list":
            option_index = event.option_index
            if option_index is not None and option_index < len(self._file_indices):
                file_index = self._file_indices[option_index]
                if file_index is not None and file_index < len(self.file_diffs):
                    selected_file = self.file_diffs[file_index]
                    diff_viewer = self.query_one("#diff-viewer", DiffViewer)
                    diff_viewer.set_file_diff(selected_file, self.existing_threads, self.draft_comments)

    def highlight_file(self, file_index: int) -> None:
        """Highlight the list row for *file_index*, skipping directory headers."""
        for option_index, mapped in enumerate(self._file_indices):
            if mapped == file_index:
                file_list = self.query_one("#file-option-list", OptionList)
                file_list.highlighted = option_index
                return

    def prompt_add_comment(self) -> None:
        diff_viewer = self.query_one("#diff-viewer", DiffViewer)
        info = diff_viewer.get_selected_line_info()
        if info:
            file_path, line_no = info
            self.post_message(self.AddCommentRequest(file_path, line_no))

    def add_draft_comment(self, path: str, line_no: int, body: str) -> None:
        """Attach a draft comment, updating the visible line when the file is shown."""
        self.draft_comments.append(DraftReviewComment(path=path, line=line_no, body=body))
        diff_viewer = self.query_one("#diff-viewer", DiffViewer)
        if diff_viewer.file_diff is not None and diff_viewer.file_diff.display_path == path:
            diff_viewer.add_pending_comment(line_no, body)

    def filter_files(self, query: str) -> int:
        self._full_file_diffs = self.file_diffs[:]
        query_lower = query.lower()
        matching = [f for f in self.file_diffs if query_lower in f.display_path.lower()]
        self.file_diffs = matching
        self._render_file_list()
        return len(matching)

    def clear_filter(self) -> None:
        if hasattr(self, '_full_file_diffs') and self._full_file_diffs:
            self.file_diffs = self._full_file_diffs[:]
            self._full_file_diffs = []
            self._render_file_list()
