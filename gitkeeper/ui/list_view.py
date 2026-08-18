from typing import List, Optional
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import OptionList
from textual.widgets.option_list import Option

from gitkeeper.scoring.calculator import TriageTier
from gitkeeper.scoring.pipeline import ScoredPullRequest, queue_sort_key


TIER_LABELS = {
    TriageTier.T0: ("T0", "bold red"),
    TriageTier.T1: ("T1", "bold yellow"),
    TriageTier.T2: ("T2", "white"),
    TriageTier.T3: ("T3", "bright_black"),
}


def _tier_style(tier: TriageTier) -> tuple[str, str]:
    label, style = TIER_LABELS.get(tier, TIER_LABELS[TriageTier.T3])
    return label, style


def _pr_number_text(number: int, url: Optional[str]) -> Text:
    """Build the PR number span, hyperlinking to the PR URL when available."""
    if url:
        return Text(f"#{number} ", style=f"bold cyan link {url}")
    return Text(f"#{number} ", style="bold cyan")


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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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
        # Sort actionable PRs by the shared pipeline key (tier, heat, size, ties)
        self.active_prs = sorted(actionable_prs, key=queue_sort_key)

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
            tier = item.score.tier
            label, style = _tier_style(tier)
            reason = item.score.reasons[0] if item.score.reasons else "actionable"

            text = Text()
            text.append(f"[{label}] ", style=f"bold {style}")
            text.append_text(_pr_number_text(item.pr.number, item.pr.url))
            text.append(f"{item.pr.repo_name_with_owner.split('/')[-1]}\n", style="magenta")
            text.append(f"     {item.pr.title[:22]} ({reason})", style="white")

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

    def filter_by_title(self, query: str) -> int:
        self._full_active_prs = self.active_prs[:]
        query_lower = query.lower()
        matching = [p for p in self.active_prs if query_lower in p.pr.title.lower()]
        self.active_prs = matching
        option_list = self.query_one("#pr-option-list", OptionList)
        option_list.clear_options()
        self._populate_list(option_list, matching)
        if matching:
            option_list.highlighted = 0
            self.post_message(self.PRSelected(matching[0]))
        return len(matching)

    def clear_filter(self) -> None:
        if hasattr(self, '_full_active_prs') and self._full_active_prs:
            self.active_prs = self._full_active_prs[:]
            self._full_active_prs = []
            option_list = self.query_one("#pr-option-list", OptionList)
            option_list.clear_options()
            self._populate_list(option_list, self.active_prs)
            if self.active_prs:
                option_list.highlighted = 0
                self.post_message(self.PRSelected(self.active_prs[0]))
