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
from gitkeeper.github.client import DraftReviewComment
from gitkeeper.ui.modals import InlineCommentModal


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
        self._rendered_lines: List[DiffLine] = []

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
        header.update(f"⠋ {text}")
        loading_text = Text(f"\n  ⠋ Loading diff lines from GitHub...\n", style="dim italic")
        options.add_option(Option(loading_text, disabled=True))

    def show_error(self, message: str) -> None:
        """Display an error state in the diff pane."""
        header = self.query_one("#diff-header", Label)
        options = self.query_one("#diff-options", OptionList)
        options.clear_options()
        self._rendered_lines = []
        self.file_diff = None

        header.update("⚠ Diff unavailable")
        err_text = Text(f"\n  ⚠ Failed to load diff: {message}\n", style="bold red")
        options.add_option(Option(err_text, disabled=True))

    def set_file_diff(self, file_diff: Optional[FileDiff], draft_comments: Optional[List[DraftReviewComment]] = None) -> None:
        self.file_diff = file_diff
        header = self.query_one("#diff-header", Label)
        options = self.query_one("#diff-options", OptionList)
        options.clear_options()
        self._rendered_lines = []

        if not file_diff:
            header.update("No file selected")
            return

        header.update(f"File: {file_diff.display_path}")
        lines = file_diff.all_lines
        self._rendered_lines = lines

        comments_by_line: Dict[int, List[str]] = {}
        if draft_comments:
            for c in draft_comments:
                if c.path == file_diff.display_path:
                    comments_by_line.setdefault(c.line, []).append(c.body)

        for idx, line in enumerate(lines):
            # Format diff line
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

            # Check if comments exist on this line
            target_line = line.new_line_no if line.new_line_no is not None else line.old_line_no
            if target_line and target_line in comments_by_line:
                for c_body in comments_by_line[target_line]:
                    rich_text.append(f"\n      💬 Pending Comment: {c_body}", style="bold yellow on #332200")

            options.add_option(Option(rich_text, id=f"line_{idx}"))

    def get_selected_line_info(self) -> Optional[tuple[str, int]]:
        if not self.file_diff:
            return None
        options = self.query_one("#diff-options", OptionList)
        idx = options.highlighted
        if idx is None or idx >= len(self._rendered_lines):
            return None
        line = self._rendered_lines[idx]
        target_line = line.new_line_no if line.new_line_no is not None else line.old_line_no
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


class PRDiffView(Widget):
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
        file_list = self.query_one("#file-option-list", OptionList)
        file_list.clear_options()
        file_list.add_option(Option("⠋ Loading files...", disabled=True))

        diff_viewer = self.query_one("#diff-viewer", DiffViewer)
        diff_viewer.show_loading(pr_identifier)

    def show_error(self, message: str) -> None:
        """Set the diff view into an error state."""
        self.file_diffs = []
        self.draft_comments = []
        file_list = self.query_one("#file-option-list", OptionList)
        file_list.clear_options()
        file_list.add_option(Option("⚠ Error loading files", disabled=True))

        diff_viewer = self.query_one("#diff-viewer", DiffViewer)
        diff_viewer.show_error(message)

    def load_diff(self, diff_text: str, draft_comments: Optional[List[DraftReviewComment]] = None) -> None:
        self.file_diffs = UnifiedDiffParser.parse(diff_text)
        self.draft_comments = draft_comments or []

        file_list = self.query_one("#file-option-list", OptionList)
        file_list.clear_options()

        for idx, fd in enumerate(self.file_diffs):
            badge = "[MOD]"
            if fd.is_new:
                badge = "[ADD]"
            elif fd.is_deleted:
                badge = "[DEL]"
            elif fd.is_renamed:
                badge = "[REN]"
            file_list.add_option(Option(f"{badge} {fd.display_path}", id=f"file_{idx}"))

        if self.file_diffs:
            file_list.highlighted = 0
            diff_viewer = self.query_one("#diff-viewer", DiffViewer)
            diff_viewer.set_file_diff(self.file_diffs[0], self.draft_comments)
        else:
            diff_viewer = self.query_one("#diff-viewer", DiffViewer)
            diff_viewer.set_file_diff(None, self.draft_comments)

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        if event.option_list.id == "file-option-list":
            if event.option_index is not None and event.option_index < len(self.file_diffs):
                selected_file = self.file_diffs[event.option_index]
                diff_viewer = self.query_one("#diff-viewer", DiffViewer)
                diff_viewer.set_file_diff(selected_file, self.draft_comments)

    def prompt_add_comment(self) -> None:
        diff_viewer = self.query_one("#diff-viewer", DiffViewer)
        info = diff_viewer.get_selected_line_info()
        if info:
            file_path, line_no = info
            self.post_message(self.AddCommentRequest(file_path, line_no))

    def filter_files(self, query: str) -> int:
        self._full_file_diffs = self.file_diffs[:]
        query_lower = query.lower()
        matching = [f for f in self.file_diffs if query_lower in f.display_path.lower()]
        self.file_diffs = matching
        file_list = self.query_one("#file-option-list", OptionList)
        file_list.clear_options()
        for idx, fd in enumerate(matching):
            badge = "[MOD]"
            if fd.is_new:
                badge = "[ADD]"
            elif fd.is_deleted:
                badge = "[DEL]"
            elif fd.is_renamed:
                badge = "[REN]"
            file_list.add_option(Option(f"{badge} {fd.display_path}", id=f"file_{idx}"))
        if matching:
            file_list.highlighted = 0
            diff_viewer = self.query_one("#diff-viewer", DiffViewer)
            diff_viewer.set_file_diff(matching[0], self.draft_comments)
        return len(matching)

    def clear_filter(self) -> None:
        if hasattr(self, '_full_file_diffs') and self._full_file_diffs:
            self.file_diffs = self._full_file_diffs[:]
            self._full_file_diffs = []
            file_list = self.query_one("#file-option-list", OptionList)
            file_list.clear_options()
            for idx, fd in enumerate(self.file_diffs):
                badge = "[MOD]"
                if fd.is_new:
                    badge = "[ADD]"
                elif fd.is_deleted:
                    badge = "[DEL]"
                elif fd.is_renamed:
                    badge = "[REN]"
                file_list.add_option(Option(f"{badge} {fd.display_path}", id=f"file_{idx}"))
            if self.file_diffs:
                file_list.highlighted = 0
                diff_viewer = self.query_one("#diff-viewer", DiffViewer)
                diff_viewer.set_file_diff(self.file_diffs[0], self.draft_comments)
