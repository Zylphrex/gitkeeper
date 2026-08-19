from datetime import datetime
from typing import Dict, List, Optional
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.events import Resize
from textual.screen import ModalScreen
from textual.widgets import Footer, Input, Label, OptionList

from gitkeeper.config import Config
from gitkeeper.github.client import DraftReviewComment, GitHubGraphQLClient, PullRequestData
from gitkeeper.repos import RepoLocator
from gitkeeper.scoring.pipeline import RelevancePipeline, ScoredPullRequest
from gitkeeper.ui.diff_view import PRDiffView
from gitkeeper.ui.header import AppHeader
from gitkeeper.ui.list_view import PRListView
from gitkeeper.ui.modals import InlineCommentModal, SubmitReviewModal
from gitkeeper.ui.overview_view import PROverviewView

ZONE_PR_LIST = "pr-list"
ZONE_RIGHT_PRIMARY = "right-primary"
ZONE_RIGHT_SECONDARY = "right-secondary"

WIDGET_TO_ZONE = {
    "pr-option-list": ZONE_PR_LIST,
    "file-option-list": ZONE_RIGHT_PRIMARY,
    "diff-options": ZONE_RIGHT_SECONDARY,
}

FOCUS_GRAPH = {
    ZONE_PR_LIST: {"left": None, "right": ZONE_RIGHT_PRIMARY},
    ZONE_RIGHT_PRIMARY: {"left": ZONE_PR_LIST, "right": ZONE_RIGHT_SECONDARY},
    ZONE_RIGHT_SECONDARY: {"left": ZONE_RIGHT_PRIMARY, "right": None},
}


class GitkeeperApp(App):
    """GitKeeper TUI application for interactive PR triage and review."""

    CSS = """
    Screen {
        background: $background;
    }

    #main-container {
        height: 1fr;
    }

    #right-tabs {
        width: 1fr;
        height: 1fr;
    }

    #status-bar {
        background: $panel;
        color: $text-muted;
        height: 1;
        padding: 0 1;
        dock: bottom;
    }

    #search-input {
        dock: bottom;
        height: 3;
        display: none;
    }

    #search-input.-active {
        display: block;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh_queue", "Refresh"),
        Binding("tab", "switch_focus", "Switch Pane", show=False),
        Binding("c", "comment_action", "Comment"),
        Binding("s", "submit_review", "Submit Review"),
        Binding("o", "open_browser", "Open in Browser"),
        Binding("j", "vim_down", "Down", show=False),
        Binding("down", "vim_down", "Down", show=False),
        Binding("k", "vim_up", "Up", show=False),
        Binding("up", "vim_up", "Up", show=False),
        Binding("h", "focus_left", "Focus Left", show=False),
        Binding("left", "focus_left", "Focus Left", show=False),
        Binding("l", "focus_right", "Focus Right", show=False),
        Binding("right", "focus_right", "Focus Right", show=False),
        Binding("g,g", "vim_top", "Top", show=False),
        Binding("G", "vim_bottom", "Bottom", show=False),
        Binding("ctrl+d", "page_down", "Page Down", show=False),
        Binding("ctrl+u", "page_up", "Page Up", show=False),
        Binding("/", "search", "Search", show=False),
        Binding("n", "next_match", "Next Match", show=False),
        Binding("N", "prev_match", "Prev Match", show=False),
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(
        self,
        config: Config,
        client: Optional[GitHubGraphQLClient] = None,
        scored_prs: Optional[List[ScoredPullRequest]] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.title = "gitkeeper"
        self.sub_title = "PR Review & Triage"
        self.config = config
        self.client = client
        self.initial_scored_prs = scored_prs
        self.current_scored_pr: Optional[ScoredPullRequest] = None
        self.cached_diffs: Dict[str, str] = {}
        self.draft_comments: Dict[str, List[DraftReviewComment]] = {}
        self._diff_loading_key: Optional[str] = None
        self.search_query = ""
        self.search_results: List[int] = []
        self.search_index = 0
        self._search_zone: Optional[str] = None

    def compose(self) -> ComposeResult:
        yield AppHeader(id="app-header")
        with Horizontal(id="main-container"):
            yield PRListView(id="pr-list-view")
            with Vertical(id="right-tabs"):
                yield PRDiffView(id="pr-diff-view")
            yield PROverviewView(id="pr-overview-view")
        yield Input(id="search-input", placeholder="/ — search (Enter to confirm, Esc to cancel)")
        yield Label("Ready", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        if self.initial_scored_prs is not None:
            self._load_scored_prs(self.initial_scored_prs)
        else:
            self.action_refresh_queue()

    def on_resize(self, event: Resize) -> None:
        try:
            self.query_one("#pr-list-view", PRListView).refresh_row_width(event.size.width)
        except Exception:
            pass

    def _load_scored_prs(self, scored_prs: List[ScoredPullRequest]) -> None:
        pr_list_view = self.query_one("#pr-list-view", PRListView)
        preserve_key = None
        if self.current_scored_pr:
            preserve_key = f"{self.current_scored_pr.pr.repo_name_with_owner}#{self.current_scored_pr.pr.number}"

        pr_list_view.set_pull_requests(scored_prs, preserve_pr_key=preserve_key)
        status_bar = self.query_one("#status-bar", Label)
        status_bar.update(f"Loaded {len(scored_prs)} review requests.")
        selected = pr_list_view.get_selected_pr()
        if selected:
            self._select_pr(selected)
        try:
            option_list = self.query_one("#pr-option-list", OptionList)
            option_list.focus()
        except Exception:
            pass

    @on(PRListView.PRSelected)
    def on_pr_list_view_pr_selected(self, event: PRListView.PRSelected) -> None:
        self._select_pr(event.scored_pr)

    def _select_pr(self, scored_pr: ScoredPullRequest) -> None:
        if self.current_scored_pr is scored_pr:
            return
        self.current_scored_pr = scored_pr
        try:
            overview_view = self.query_one("#pr-overview-view", PROverviewView)
            overview_view.update_pr(scored_pr)
        except Exception:
            pass

        # Clear or load diff
        pr_key = f"{scored_pr.pr.repo_name_with_owner}#{scored_pr.pr.number}"
        if pr_key in self.cached_diffs:
            self._display_cached_diff(pr_key)
        elif self._diff_loading_key == pr_key:
            return
        else:
            self._diff_loading_key = pr_key
            try:
                diff_view = self.query_one("#pr-diff-view", PRDiffView)
                diff_view.show_loading(f"#{scored_pr.pr.number}")
                self._fetch_diff_for_pr(scored_pr.pr)
            except Exception:
                self._diff_loading_key = None
                pass

    def _display_cached_diff(self, pr_key: str) -> None:
        if not self.current_scored_pr:
            return
        curr_key = f"{self.current_scored_pr.pr.repo_name_with_owner}#{self.current_scored_pr.pr.number}"
        if pr_key != curr_key:
            return

        diff_view = self.query_one("#pr-diff-view", PRDiffView)
        diff_text = self.cached_diffs.get(pr_key, "")
        comments = self.draft_comments.get(pr_key, [])
        diff_view.load_diff(diff_text, comments)
        if self._diff_loading_key == pr_key:
            self._diff_loading_key = None

    def _display_diff_error(self, pr_key: str, message: str) -> None:
        if not self.current_scored_pr:
            return
        curr_key = f"{self.current_scored_pr.pr.repo_name_with_owner}#{self.current_scored_pr.pr.number}"
        if pr_key != curr_key:
            return

        diff_view = self.query_one("#pr-diff-view", PRDiffView)
        diff_view.show_error(message)
        if self._diff_loading_key == pr_key:
            self._diff_loading_key = None

    @work(exclusive=True, thread=True)
    def _fetch_diff_for_pr(self, pr: PullRequestData) -> None:
        pr_key = f"{pr.repo_name_with_owner}#{pr.number}"
        if not self.client:
            return

        try:
            diff_text = self.client.get_pull_request_diff(pr.repo_name_with_owner, pr.number)
            self.cached_diffs[pr_key] = diff_text
            self.app.call_from_thread(self._display_cached_diff, pr_key)
        except Exception as exc:
            self.app.call_from_thread(self._display_diff_error, pr_key, str(exc))
            self.app.call_from_thread(self._set_status, f"Error fetching diff: {exc}")

    def _set_status(self, text: str) -> None:
        status_bar = self.query_one("#status-bar", Label)
        status_bar.update(text)

    def _guard_vim_action(self) -> bool:
        """Return True when Vim actions should be suppressed (modal active)."""
        if self.screen is None:
            return True
        return isinstance(self.screen, ModalScreen)

    def _focused_widget(self) -> Optional[object]:
        if self.screen is None:
            return None
        return self.screen.focused

    def _dispatch_option_or_scroll(self, option_attr: str, scroll_attr: str) -> None:
        focused = self._focused_widget()
        if focused is None:
            return
        if isinstance(focused, OptionList):
            try:
                getattr(focused, option_attr)()
            except Exception:
                pass
        elif isinstance(focused, VerticalScroll):
            try:
                getattr(focused, scroll_attr)()
            except Exception:
                pass

    def action_vim_down(self) -> None:
        if self._guard_vim_action():
            return
        self._dispatch_option_or_scroll("action_cursor_down", "action_scroll_down")

    def action_vim_up(self) -> None:
        if self._guard_vim_action():
            return
        self._dispatch_option_or_scroll("action_cursor_up", "action_scroll_up")

    def action_vim_top(self) -> None:
        if self._guard_vim_action():
            return
        self._dispatch_option_or_scroll("action_first", "action_scroll_home")

    def action_vim_bottom(self) -> None:
        if self._guard_vim_action():
            return
        self._dispatch_option_or_scroll("action_last", "action_scroll_end")

    def action_page_down(self) -> None:
        if self._guard_vim_action():
            return
        self._dispatch_option_or_scroll("action_page_down", "action_page_down")

    def action_page_up(self) -> None:
        if self._guard_vim_action():
            return
        self._dispatch_option_or_scroll("action_page_up", "action_page_up")

    def _current_zone(self) -> Optional[str]:
        focused = self._focused_widget()
        if focused is not None:
            if focused.id is not None:
                return WIDGET_TO_ZONE.get(focused.id)
            return None
        try:
            pr_list = self.query_one("#pr-option-list", OptionList)
            if pr_list.highlighted is not None:
                return ZONE_PR_LIST
        except Exception:
            pass
        return None

    def _widget_for_zone(self, zone: str) -> Optional[str]:
        if zone == ZONE_PR_LIST:
            return "pr-option-list"
        if zone == ZONE_RIGHT_PRIMARY:
            return "file-option-list"
        if zone == ZONE_RIGHT_SECONDARY:
            return "diff-options"
        return None

    def _move_focus(self, direction: str) -> None:
        if self._guard_vim_action():
            return
        zone = self._current_zone()
        if zone is None:
            return
        target_zone = FOCUS_GRAPH[zone][direction]
        if target_zone is None:
            return
        target_widget_id = self._widget_for_zone(target_zone)
        if target_widget_id is None:
            return
        try:
            target = self.query_one(f"#{target_widget_id}")
        except Exception:
            return
        if self.search_query:
            self._clear_active_filter()
        self._clear_search_state()
        target.focus()

    def action_focus_left(self) -> None:
        self._move_focus("left")

    def action_focus_right(self) -> None:
        self._move_focus("right")

    def action_cancel(self) -> None:
        search_input = self.query_one("#search-input", Input)
        if search_input.has_class("-active"):
            self._hide_search()
        if self.search_query:
            self._clear_active_filter()
            self._clear_search_state()
        self._set_status("Search cleared.")

    def action_search(self) -> None:
        if self._guard_vim_action():
            return
        self._search_zone = self._current_zone()
        search_input = self.query_one("#search-input", Input)
        search_input.value = ""
        search_input.add_class("-active")
        search_input.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "search-input":
            return
        query = event.value.strip()
        self._hide_search()
        if not query:
            self._set_status("Search cleared.")
            return
        self._apply_search(query)

    def _hide_search(self) -> None:
        search_input = self.query_one("#search-input", Input)
        search_input.remove_class("-active")
        search_input.value = ""
        zone = self._search_zone
        if zone:
            target_id = self._widget_for_zone(zone)
            if target_id:
                try:
                    self.query_one(f"#{target_id}").focus()
                except Exception:
                    pass

    def _apply_search(self, query: str) -> None:
        zone = self._search_zone or self._current_zone()
        self.search_query = query
        self.search_results = []
        self.search_index = 0

        if zone == ZONE_PR_LIST:
            pr_list_view = self.query_one("#pr-list-view", PRListView)
            matches = pr_list_view.filter_by_title(query)
            if matches == 0:
                pr_list_view.clear_filter()
            self.search_results = list(range(matches))
            self._set_status(f"Search '{query}': {matches} PR(s) match.")
        elif zone == ZONE_RIGHT_PRIMARY:
            diff_view = self.query_one("#pr-diff-view", PRDiffView)
            matches = diff_view.filter_files(query)
            if matches == 0:
                diff_view.clear_filter()
            self.search_results = list(range(matches))
            self._set_status(f"Search '{query}': {matches} file(s) match.")
        elif zone == ZONE_RIGHT_SECONDARY:
            diff_viewer = self.query_one("#diff-viewer")
            matches = diff_viewer.find_matching_lines(query)
            self.search_results = matches
            if matches:
                self.search_index = 0
                self._jump_to_search_result()
                self._set_status(f"Search '{query}': {len(matches)} matching line(s).")
            else:
                self._set_status(f"No lines match '{query}'.")
        else:
            self._set_status(f"Search '{query}': no matches.")

    def _clear_search_state(self) -> None:
        self.search_query = ""
        self.search_results = []
        self.search_index = 0
        self._search_zone = None

    def _clear_active_filter(self) -> None:
        zone = self._search_zone
        if zone == ZONE_PR_LIST:
            try:
                self.query_one("#pr-list-view", PRListView).clear_filter()
            except Exception:
                pass
        elif zone == ZONE_RIGHT_PRIMARY:
            try:
                self.query_one("#pr-diff-view", PRDiffView).clear_filter()
            except Exception:
                pass

    def action_next_match(self) -> None:
        if self._guard_vim_action():
            return
        if not self.search_results:
            return
        self.search_index = (self.search_index + 1) % len(self.search_results)
        self._jump_to_search_result()

    def action_prev_match(self) -> None:
        if self._guard_vim_action():
            return
        if not self.search_results:
            return
        self.search_index = (self.search_index - 1) % len(self.search_results)
        self._jump_to_search_result()

    def _jump_to_search_result(self) -> None:
        zone = self._search_zone
        if zone is None or not self.search_results:
            return
        idx = self.search_results[self.search_index]
        if zone == ZONE_PR_LIST:
            try:
                option_list = self.query_one("#pr-option-list", OptionList)
                option_list.highlighted = idx
            except Exception:
                pass
        elif zone == ZONE_RIGHT_PRIMARY:
            try:
                diff_view = self.query_one("#pr-diff-view", PRDiffView)
                diff_view.highlight_file(idx)
            except Exception:
                pass
        elif zone == ZONE_RIGHT_SECONDARY:
            try:
                diff_options = self.query_one("#diff-options", OptionList)
                diff_options.highlighted = idx
            except Exception:
                pass

    def action_comment_action(self) -> None:
        diff_view = self.query_one("#pr-diff-view", PRDiffView)
        diff_view.prompt_add_comment()

    def on_prdiff_view_add_comment_request(self, event: PRDiffView.AddCommentRequest) -> None:
        if not self.current_scored_pr:
            return

        def handle_comment_result(comment_text: str) -> None:
            if not comment_text:
                return
            pr_key = f"{self.current_scored_pr.pr.repo_name_with_owner}#{self.current_scored_pr.pr.number}"
            draft = DraftReviewComment(path=event.file_path, line=event.line_no, body=comment_text)
            self.draft_comments.setdefault(pr_key, []).append(draft)
            diff_view = self.query_one("#pr-diff-view", PRDiffView)
            diff_view.add_draft_comment(event.file_path, event.line_no, comment_text)
            self._set_status(f"Added comment on {event.file_path}:{event.line_no}")

        self.push_screen(
            InlineCommentModal(event.file_path, event.line_no),
            handle_comment_result,
        )

    def action_open_browser(self) -> None:
        if self._guard_vim_action():
            return
        if not self.current_scored_pr:
            self._set_status("No PR selected.")
            return
        url = self.current_scored_pr.pr.url
        if not url:
            self._set_status("No URL available for this PR.")
            return
        self.app.open_url(url)
        self._set_status(f"Opening {url} in browser...")

    def action_submit_review(self) -> None:
        if not self.current_scored_pr:
            self._set_status("No PR selected.")
            return

        pr = self.current_scored_pr.pr
        pr_key = f"{pr.repo_name_with_owner}#{pr.number}"
        pending = self.draft_comments.get(pr_key, [])

        def handle_modal_result(result: Optional[dict]) -> None:
            if not result:
                return
            event_type = result["event"]
            body = result["body"] or None
            self._submit_review_worker(pr.id, event_type, body, pending, pr_key)

        self.push_screen(
            SubmitReviewModal(pr.title, len(pending)),
            handle_modal_result,
        )

    @work(exclusive=True, thread=True)
    def _submit_review_worker(
        self,
        pr_id: str,
        event: str,
        body: Optional[str],
        comments: List[DraftReviewComment],
        pr_key: str,
    ) -> None:
        if not self.client:
            self.app.call_from_thread(self._set_status, "Error: No GitHub client available.")
            return

        self.app.call_from_thread(self._set_status, f"Submitting {event} review...")
        try:
            self.client.add_pull_request_review(
                pull_request_id=pr_id,
                event=event,
                body=body,
                comments=comments,
            )
            # Clear draft comments on successful submission
            if pr_key in self.draft_comments:
                del self.draft_comments[pr_key]

            self.app.call_from_thread(self._set_status, f"✓ Review submitted ({event}) successfully.")
            self.app.call_from_thread(self.action_refresh_queue)
        except Exception as exc:
            self.app.call_from_thread(self._set_status, f"Error submitting review: {exc}")

    def _set_header_loading(self, message: str) -> None:
        try:
            header = self.query_one("#app-header", AppHeader)
            header.set_loading(message)
        except Exception:
            pass

    def _set_header_idle(self, message: str = "Ready", refreshed_at: Optional[datetime] = None) -> None:
        try:
            header = self.query_one("#app-header", AppHeader)
            header.set_idle(message, refreshed_at=refreshed_at)
        except Exception:
            pass

    def _set_header_error(self, message: str) -> None:
        try:
            header = self.query_one("#app-header", AppHeader)
            header.set_error(message)
        except Exception:
            pass

    @work(exclusive=True, thread=True)
    def action_refresh_queue(self) -> None:
        if not self.client:
            return

        self.app.call_from_thread(self._set_status, "Fetching review requests from GitHub...")
        self.app.call_from_thread(self._set_header_loading, "Fetching review requests from GitHub...")
        try:
            user = self.config.github.user
            if not user:
                try:
                    user = self.client.get_viewer_login()
                    self.config.github.user = user
                except Exception:
                    pass

            prs = self.client.fetch_pending_review_requests(user)

            self.app.call_from_thread(self._set_status, "Evaluating relevance heuristics & local repos...")
            self.app.call_from_thread(self._set_header_loading, "Evaluating relevance heuristics...")

            repo_locator = RepoLocator(self.config.repositories)
            pipeline = RelevancePipeline(self.config, repo_locator)
            scored = pipeline.process(prs)

            now = datetime.now()
            self.app.call_from_thread(self._load_scored_prs, scored)
            self.app.call_from_thread(self._set_header_idle, "Ready", refreshed_at=now)
        except Exception as exc:
            self.app.call_from_thread(self._set_status, f"Error refreshing queue: {exc}")
            self.app.call_from_thread(self._set_header_error, f"Refresh failed: {exc}")
