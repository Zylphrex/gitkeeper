from typing import Dict, List, Optional
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Footer, Header, Label, TabbedContent, TabPane

from gitkeeper.config import Config
from gitkeeper.github.client import DraftReviewComment, GitHubGraphQLClient, PullRequestData
from gitkeeper.repos import RepoLocator
from gitkeeper.scoring.pipeline import RelevancePipeline, ScoredPullRequest
from gitkeeper.ui.diff_view import PRDiffView
from gitkeeper.ui.list_view import PRListView
from gitkeeper.ui.modals import InlineCommentModal, SubmitReviewModal
from gitkeeper.ui.overview_view import PROverviewView


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
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh_queue", "Refresh"),
        Binding("tab", "switch_focus", "Switch Pane", show=False),
        Binding("1", "tab_overview", "Overview"),
        Binding("2", "tab_diff", "Files & Diff"),
        Binding("c", "comment_action", "Comment"),
        Binding("a", "quick_approve", "Approve"),
        Binding("s", "submit_review", "Submit Review"),
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

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main-container"):
            yield PRListView(
                min_threshold=self.config.heuristics.min_score_threshold,
                id="pr-list-view",
            )
            with TabbedContent(id="right-tabs"):
                with TabPane("Overview", id="tab-overview"):
                    yield PROverviewView(id="pr-overview-view")
                with TabPane("Files & Diff", id="tab-diff"):
                    yield PRDiffView(id="pr-diff-view")
        yield Label("Ready", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        if self.initial_scored_prs is not None:
            self._load_scored_prs(self.initial_scored_prs)
        else:
            self.action_refresh_queue()

    def _load_scored_prs(self, scored_prs: List[ScoredPullRequest]) -> None:
        pr_list_view = self.query_one("#pr-list-view", PRListView)
        pr_list_view.set_pull_requests(scored_prs)
        status_bar = self.query_one("#status-bar", Label)
        status_bar.update(f"Loaded {len(scored_prs)} review requests.")
        if pr_list_view.active_prs:
            self._select_pr(pr_list_view.active_prs[0])
        elif pr_list_view.ambient_prs:
            self._select_pr(pr_list_view.ambient_prs[0])

    def on_pr_list_view_pr_selected(self, event: PRListView.PRSelected) -> None:
        self._select_pr(event.scored_pr)

    def _select_pr(self, scored_pr: ScoredPullRequest) -> None:
        self.current_scored_pr = scored_pr
        overview_view = self.query_one("#pr-overview-view", PROverviewView)
        overview_view.update_pr(scored_pr)

        # Clear or load diff
        pr_key = f"{scored_pr.pr.repo_name_with_owner}#{scored_pr.pr.number}"
        if pr_key in self.cached_diffs:
            self._display_cached_diff(pr_key)
        else:
            self._fetch_diff_for_pr(scored_pr.pr)

    def _display_cached_diff(self, pr_key: str) -> None:
        diff_view = self.query_one("#pr-diff-view", PRDiffView)
        diff_text = self.cached_diffs.get(pr_key, "")
        comments = self.draft_comments.get(pr_key, [])
        diff_view.load_diff(diff_text, comments)

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
            self.app.call_from_thread(self._set_status, f"Error fetching diff: {exc}")

    def _set_status(self, text: str) -> None:
        status_bar = self.query_one("#status-bar", Label)
        status_bar.update(text)

    def action_tab_overview(self) -> None:
        tabs = self.query_one("#right-tabs", TabbedContent)
        tabs.active = "tab-overview"

    def action_tab_diff(self) -> None:
        tabs = self.query_one("#right-tabs", TabbedContent)
        tabs.active = "tab-diff"

    def action_comment_action(self) -> None:
        tabs = self.query_one("#right-tabs", TabbedContent)
        if tabs.active == "tab-diff":
            diff_view = self.query_one("#pr-diff-view", PRDiffView)
            diff_view.prompt_add_comment()
        else:
            self.action_submit_review()

    def on_pr_diff_view_add_comment_request(self, event: PRDiffView.AddCommentRequest) -> None:
        if not self.current_scored_pr:
            return

        def handle_comment_result(comment_text: str) -> None:
            if not comment_text:
                return
            pr_key = f"{self.current_scored_pr.pr.repo_name_with_owner}#{self.current_scored_pr.pr.number}"
            draft = DraftReviewComment(path=event.file_path, line=event.line_no, body=comment_text)
            self.draft_comments.setdefault(pr_key, []).append(draft)
            self._display_cached_diff(pr_key)
            self._set_status(f"Added comment on {event.file_path}:{event.line_no}")

        self.push_screen(
            InlineCommentModal(event.file_path, event.line_no),
            handle_comment_result,
        )

    def action_quick_approve(self) -> None:
        if not self.current_scored_pr:
            self._set_status("No PR selected to approve.")
            return

        pr = self.current_scored_pr.pr
        pr_key = f"{pr.repo_name_with_owner}#{pr.number}"
        pending_comments = self.draft_comments.get(pr_key, [])

        self._submit_review_worker(pr.id, "APPROVE", "LGTM!", pending_comments, pr_key)

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

    @work(exclusive=True, thread=True)
    def action_refresh_queue(self) -> None:
        if not self.client:
            return

        self.app.call_from_thread(self._set_status, "Fetching review requests from GitHub...")
        try:
            user = self.config.github.user
            if not user:
                try:
                    user = self.client.get_viewer_login()
                    self.config.github.user = user
                except Exception:
                    pass

            prs = self.client.fetch_pending_review_requests(user)
            repo_locator = RepoLocator(self.config.repositories)
            pipeline = RelevancePipeline(self.config, repo_locator)
            scored = pipeline.process(prs)

            self.app.call_from_thread(self._load_scored_prs, scored)
        except Exception as exc:
            self.app.call_from_thread(self._set_status, f"Error refreshing queue: {exc}")
