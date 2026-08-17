from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, OptionList, RadioButton, RadioSet, TextArea
from textual.widgets.option_list import Option


class InlineCommentModal(ModalScreen[str]):
    """Modal dialog for adding an inline review comment to a diff line."""

    DEFAULT_CSS = """
    InlineCommentModal {
        align: center middle;
    }

    #comment-dialog {
        padding: 1 2;
        width: 70;
        height: auto;
        border: thick $primary;
        background: $surface;
    }

    #comment-title {
        text-style: bold;
        margin-bottom: 1;
    }

    #comment-input {
        height: 6;
        margin-bottom: 1;
    }

    #comment-buttons {
        align: right middle;
        height: 3;
    }

    #comment-buttons Button {
        margin-left: 1;
    }
    """

    def __init__(self, file_path: str, line_no: int, initial_text: str = ""):
        super().__init__()
        self.file_path = file_path
        self.line_no = line_no
        self.initial_text = initial_text

    def compose(self) -> ComposeResult:
        with Vertical(id="comment-dialog"):
            yield Label(f"Add Comment on {self.file_path}:{self.line_no}", id="comment-title")
            yield TextArea(self.initial_text, id="comment-input")
            with Horizontal(id="comment-buttons"):
                yield Button("Cancel", id="btn-cancel", variant="default")
                yield Button("Save Comment", id="btn-save", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            text_area = self.query_one("#comment-input", TextArea)
            comment_text = text_area.text.strip()
            self.dismiss(comment_text)
        else:
            self.dismiss("")

    def key_escape(self) -> None:
        self.dismiss("")


class SubmitReviewModal(ModalScreen[dict]):
    """Modal dialog for choosing review verdict and submitting summary."""

    DEFAULT_CSS = """
    SubmitReviewModal {
        align: center middle;
    }

    #review-dialog {
        padding: 1 2;
        width: 75;
        height: auto;
        border: thick $primary;
        background: $surface;
    }

    #review-title {
        text-style: bold;
        margin-bottom: 1;
    }

    #review-event-label {
        margin-top: 1;
        text-style: bold;
    }

    #review-radioset {
        margin-bottom: 1;
    }

    #review-body-input {
        height: 6;
        margin-bottom: 1;
    }

    #review-buttons {
        align: right middle;
        height: 3;
    }

    #review-buttons Button {
        margin-left: 1;
    }
    """

    def __init__(self, pr_title: str, pending_comments_count: int = 0):
        super().__init__()
        self.pr_title = pr_title
        self.pending_comments_count = pending_comments_count

    def compose(self) -> ComposeResult:
        with Vertical(id="review-dialog"):
            yield Label(f"Submit Review: {self.pr_title}", id="review-title")
            if self.pending_comments_count > 0:
                yield Label(f"[cyan]{self.pending_comments_count} inline comment(s) will be included in this submission.[/cyan]")

            yield Label("Review Decision:", id="review-event-label")
            with RadioSet(id="review-radioset"):
                yield RadioButton("Approve (APPROVE)", value=True, id="radio-approve")
                yield RadioButton("Request Changes (REQUEST_CHANGES)", id="radio-request-changes")
                yield RadioButton("Comment (COMMENT)", id="radio-comment")

            yield Label("Summary / Feedback:")
            yield TextArea("", id="review-body-input")

            with Horizontal(id="review-buttons"):
                yield Button("Cancel", id="btn-cancel-review", variant="default")
                yield Button("Submit Review", id="btn-submit-review", variant="success")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-submit-review":
            radios = self.query_one("#review-radioset", RadioSet)
            selected_idx = radios.pressed_index
            event_type = "APPROVE"
            if selected_idx == 1:
                event_type = "REQUEST_CHANGES"
            elif selected_idx == 2:
                event_type = "COMMENT"

            body_input = self.query_one("#review-body-input", TextArea)
            summary_body = body_input.text.strip()

            self.dismiss({
                "event": event_type,
                "body": summary_body,
            })
        else:
            self.dismiss(None)

    def key_escape(self) -> None:
        self.dismiss(None)
