from typing import List, Optional
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, Label, OptionList, TabbedContent, TabPane
from textual.widgets.option_list import Option

from gitkeeper.scoring.pipeline import ScoredPullRequest


class PRListView(Widget):
    """Ranked PR list widget with tabs for Active Queue and Ambient PRs."""

    DEFAULT_CSS = """
    PRListView {
        width: 42;
        border-right: solid $primary;
        height: 1fr;
    }

    #pr-tabs {
        height: 1fr;
    }

    .pr-option-list {
        height: 1fr;
    }
    """

    class PRSelected(Message):
        def __init__(self, scored_pr: ScoredPullRequest):
            super().__init__()
            self.scored_pr = scored_pr

    def __init__(self, min_threshold: int = 40, **kwargs):
        super().__init__(**kwargs)
        self.min_threshold = min_threshold
        self.all_scored_prs: List[ScoredPullRequest] = []
        self.active_prs: List[ScoredPullRequest] = []
        self.ambient_prs: List[ScoredPullRequest] = []

    def compose(self) -> ComposeResult:
        with TabbedContent(id="pr-tabs"):
            with TabPane("Queue", id="tab-queue"):
                yield OptionList(id="queue-option-list", classes="pr-option-list")
            with TabPane("Ambient", id="tab-ambient"):
                yield OptionList(id="ambient-option-list", classes="pr-option-list")

    def set_pull_requests(
        self,
        scored_prs: List[ScoredPullRequest],
        preserve_pr_key: Optional[str] = None,
    ) -> None:
        self.all_scored_prs = scored_prs
        actionable_prs = [p for p in scored_prs if p.is_actionable]
        self.active_prs = [p for p in actionable_prs if p.score.total_score >= self.min_threshold]
        self.ambient_prs = [p for p in actionable_prs if p.score.total_score < self.min_threshold]

        queue_list = self.query_one("#queue-option-list", OptionList)
        ambient_list = self.query_one("#ambient-option-list", OptionList)
        tabs = self.query_one("#pr-tabs", TabbedContent)

        queue_list.clear_options()
        ambient_list.clear_options()

        self._populate_list(queue_list, self.active_prs)
        self._populate_list(ambient_list, self.ambient_prs)

        # Try to restore preserved PR selection
        if preserve_pr_key:
            # Check queue list first
            for idx, p in enumerate(self.active_prs):
                key = f"{p.pr.repo_name_with_owner}#{p.pr.number}"
                if key == preserve_pr_key:
                    tabs.active = "tab-queue"
                    queue_list.highlighted = idx
                    self.post_message(self.PRSelected(p))
                    return

            # Check ambient list next
            for idx, p in enumerate(self.ambient_prs):
                key = f"{p.pr.repo_name_with_owner}#{p.pr.number}"
                if key == preserve_pr_key:
                    tabs.active = "tab-ambient"
                    ambient_list.highlighted = idx
                    self.post_message(self.PRSelected(p))
                    return

        # Fallback to highlighting first available item
        if self.active_prs:
            tabs.active = "tab-queue"
            queue_list.highlighted = 0
            self.post_message(self.PRSelected(self.active_prs[0]))
        elif self.ambient_prs:
            tabs.active = "tab-ambient"
            ambient_list.highlighted = 0
            self.post_message(self.PRSelected(self.ambient_prs[0]))

    def _populate_list(self, option_list: OptionList, prs: List[ScoredPullRequest]) -> None:
        for idx, item in enumerate(prs):
            score = item.score.total_score
            score_color = "green" if score >= 75 else ("yellow" if score >= 50 else "white")

            text = Text()
            text.append(f"[{score:2d}] ", style=f"bold {score_color}")
            text.append(f"#{item.pr.number} ", style="bold cyan")
            text.append(f"{item.pr.repo_name_with_owner.split('/')[-1]}\n", style="magenta")
            text.append(f"     {item.pr.title[:30]}", style="white")

            option_list.add_option(Option(text, id=f"pr_{item.pr.number}_{idx}"))

    def _handle_option_selection(self, list_id: Optional[str], option_index: Optional[int]) -> None:
        if option_index is None:
            return
        if list_id == "queue-option-list":
            if option_index < len(self.active_prs):
                queue_list = self.query_one("#queue-option-list", OptionList)
                if queue_list.highlighted != option_index:
                    queue_list.highlighted = option_index
                self.post_message(self.PRSelected(self.active_prs[option_index]))
        elif list_id == "ambient-option-list":
            if option_index < len(self.ambient_prs):
                ambient_list = self.query_one("#ambient-option-list", OptionList)
                if ambient_list.highlighted != option_index:
                    ambient_list.highlighted = option_index
                self.post_message(self.PRSelected(self.ambient_prs[option_index]))

    @on(OptionList.OptionHighlighted)
    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        self._handle_option_selection(event.option_list.id, event.option_index)

    @on(OptionList.OptionSelected)
    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self._handle_option_selection(event.option_list.id, event.option_index)

    @on(TabbedContent.TabActivated)
    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        if event.tabbed_content.id != "pr-tabs":
            return
        if event.pane.id == "tab-queue":
            queue_list = self.query_one("#queue-option-list", OptionList)
            if queue_list.highlighted is None and self.active_prs:
                queue_list.highlighted = 0
            if queue_list.highlighted is not None and queue_list.highlighted < len(self.active_prs):
                self.post_message(self.PRSelected(self.active_prs[queue_list.highlighted]))
        elif event.pane.id == "tab-ambient":
            ambient_list = self.query_one("#ambient-option-list", OptionList)
            if ambient_list.highlighted is None and self.ambient_prs:
                ambient_list.highlighted = 0
            if ambient_list.highlighted is not None and ambient_list.highlighted < len(self.ambient_prs):
                self.post_message(self.PRSelected(self.ambient_prs[ambient_list.highlighted]))

    def get_selected_pr(self) -> Optional[ScoredPullRequest]:
        tabs = self.query_one("#pr-tabs", TabbedContent)
        if tabs.active == "tab-queue":
            q_list = self.query_one("#queue-option-list", OptionList)
            if q_list.highlighted is not None and q_list.highlighted < len(self.active_prs):
                return self.active_prs[q_list.highlighted]
        elif tabs.active == "tab-ambient":
            a_list = self.query_one("#ambient-option-list", OptionList)
            if a_list.highlighted is not None and a_list.highlighted < len(self.ambient_prs):
                return self.ambient_prs[a_list.highlighted]
        return None
