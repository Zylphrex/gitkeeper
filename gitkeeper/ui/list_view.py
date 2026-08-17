from typing import List, Optional
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import OptionList
from textual.widgets.option_list import Option

from gitkeeper.scoring.pipeline import ScoredPullRequest


class PRListView(Widget):
    """Ranked PR list widget displaying actionable PRs sorted by relevance score."""

    DEFAULT_CSS = """
    PRListView {
        width: 42;
        border-right: solid $primary;
        height: 1fr;
    }

    #pr-option-list {
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

    def compose(self) -> ComposeResult:
        yield OptionList(id="pr-option-list")

    def set_pull_requests(
        self,
        scored_prs: List[ScoredPullRequest],
        preserve_pr_key: Optional[str] = None,
    ) -> None:
        self.all_scored_prs = scored_prs
        actionable_prs = [p for p in scored_prs if p.is_actionable]
        # Sort actionable PRs strictly descending by relevance score
        self.active_prs = sorted(
            actionable_prs,
            key=lambda p: p.score.total_score,
            reverse=True,
        )

        option_list = self.query_one("#pr-option-list", OptionList)
        option_list.clear_options()
        self._populate_list(option_list, self.active_prs)

        # Try to restore preserved PR selection
        if preserve_pr_key:
            for idx, p in enumerate(self.active_prs):
                key = f"{p.pr.repo_name_with_owner}#{p.pr.number}"
                if key == preserve_pr_key:
                    option_list.highlighted = idx
                    self.post_message(self.PRSelected(p))
                    return

        # Fallback to highlighting first available item
        if self.active_prs:
            option_list.highlighted = 0
            self.post_message(self.PRSelected(self.active_prs[0]))

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

    def _handle_option_selection(self, option_index: Optional[int]) -> None:
        if option_index is None:
            return
        if option_index < len(self.active_prs):
            option_list = self.query_one("#pr-option-list", OptionList)
            if option_list.highlighted != option_index:
                option_list.highlighted = option_index
            self.post_message(self.PRSelected(self.active_prs[option_index]))

    @on(OptionList.OptionHighlighted)
    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        if event.option_list.id == "pr-option-list":
            self._handle_option_selection(event.option_index)

    @on(OptionList.OptionSelected)
    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id == "pr-option-list":
            self._handle_option_selection(event.option_index)

    def get_selected_pr(self) -> Optional[ScoredPullRequest]:
        option_list = self.query_one("#pr-option-list", OptionList)
        if option_list.highlighted is not None and option_list.highlighted < len(self.active_prs):
            return self.active_prs[option_list.highlighted]
        return None
