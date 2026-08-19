from typing import List, Optional
from rich.cells import cell_len
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

# Nominal usable width for a single #pr-option-list row. The pane is 42 cols;
# subtract the pane border (1), the OptionList's own border + padding (4),
# and a safety column to stay under the wrap threshold. The live budget is
# tightened in _effective_row_width whenever the list is scrollable.
ROW_WIDTH = 36
MIN_ROW_WIDTH = 8  # floor when a very narrow window squeezes the pane
ELLIPSIS = "…"


def _truncate(text: str, width: int) -> str:
    """Return *text* trimmed to *width* columns, appending an ellipsis when it overflows.

    Truncation is measured in display cells (``rich.cells.cell_len``), so wide
    glyphs (CJK, emoji) count double and never push a row past the budget.
    """
    if cell_len(text) <= width:
        return text
    ellipsis_width = cell_len(ELLIPSIS)
    keep = 0
    cells = 0
    for char in text:
        char_width = cell_len(char)
        if cells + char_width > width - ellipsis_width:
            break
        cells += char_width
        keep += 1
    return text[:keep] + ELLIPSIS


def _effective_row_width(option_list: OptionList, screen_width: Optional[int] = None) -> int:
    """Row budget in columns for one option line.

    OptionList wraps each option at its *scrollable* content width, which is
    narrower than ``content_region`` whenever a vertical scrollbar is showing;
    budget against that actual render width so truncated rows never wrap. The
    pane is nominally 42 cols wide, but when the terminal is too small for the
    fixed panes the compositor paints the list narrower than that, so clamp
    against the actual screen width (explicit *screen_width*, or the live one)
    whenever the pane would be painted off-screen.
    """
    try:
        if screen_width is None:
            screen_width = option_list.screen.size.width
        if screen_width <= 0:
            return ROW_WIDTH
        content = option_list.scrollable_content_region
        if content.width <= 0:
            content = option_list.content_region
        pane_width = content.width - option_list._get_left_gutter_width()
        if pane_width <= 0:
            return ROW_WIDTH
        available = min(pane_width, max(screen_width - 4, MIN_ROW_WIDTH))
        return max(min(ROW_WIDTH, available - 1), MIN_ROW_WIDTH)
    except Exception:
        return ROW_WIDTH


def _tier_style(tier: TriageTier) -> tuple[str, str]:
    label, style = TIER_LABELS.get(tier, TIER_LABELS[TriageTier.T3])
    return label, style


def _pr_number_text(number: int, url: Optional[str]) -> Text:
    """Build the PR number span, hyperlinking to the PR URL when available."""
    if url:
        return Text(f"#{number} ", style=f"bold cyan link {url}")
    return Text(f"#{number} ", style="bold cyan")


class _QueueOptionList(OptionList):
    """PR queue option list that signals scrollbar-visibility switches to its host.

    Textual emits no resize when the vertical scrollbar appears or disappears,
    so the row-width budget would otherwise go stale whenever the queue crosses
    the pane height without a data change.
    """

    class ScrollbarVisibilityChanged(Message):
        def __init__(self, visible: bool):
            super().__init__()
            self.visible = visible

    def watch_show_vertical_scrollbar(self, visible: bool) -> None:
        self.post_message(self.ScrollbarVisibilityChanged(visible))


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
        self._row_width: Optional[int] = None

    def compose(self) -> ComposeResult:
        yield _QueueOptionList(id="pr-option-list")

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

    def _populate_list(
        self,
        option_list: OptionList,
        prs: List[ScoredPullRequest],
        row_width: Optional[int] = None,
    ) -> None:
        if row_width is None:
            row_width = _effective_row_width(option_list)
        for idx, item in enumerate(prs):
            tier = item.score.tier
            label, style = _tier_style(tier)

            badge = f"[{label}] "
            number = f"#{item.pr.number} "
            author = f"  @{item.pr.author}"
            meta_budget = row_width - cell_len(badge) - cell_len(number)
            if cell_len(author) >= meta_budget:
                # Even a minimal handler is too long: keep the front of it.
                author = _truncate(author, meta_budget)
                repo = ""
            else:
                repo = _truncate(
                    item.pr.repo_name_with_owner.split("/")[-1],
                    meta_budget - cell_len(author),
                )

            text = Text()
            text.append(badge, style=f"bold {style}")
            text.append_text(_pr_number_text(item.pr.number, item.pr.url))
            text.append(repo, style="magenta")
            text.append(author, style="dim")
            text.append("\n")
            text.append(_truncate(item.pr.title, row_width), style="white")

            option_list.add_option(Option(text, id=f"pr_{item.pr.number}_{idx}"))

    def on_resize(self) -> None:
        """Re-measure the row budget when this widget's region changes."""
        self._remeasure_row_width()

    @on(_QueueOptionList.ScrollbarVisibilityChanged)
    def on_queue_scrollbar_visibility_changed(
        self, event: _QueueOptionList.ScrollbarVisibilityChanged
    ) -> None:
        """Re-measure when the list's scrollbar appears or disappears."""
        self._remeasure_row_width()

    def refresh_row_width(self, screen_width: Optional[int] = None) -> None:
        """Re-measure the row budget after the window size changes."""
        self._remeasure_row_width(screen_width)

    def _remeasure_row_width(self, screen_width: Optional[int] = None) -> None:
        try:
            option_list = self.query_one("#pr-option-list", OptionList)
        except Exception:
            return
        row_width = _effective_row_width(option_list, screen_width)
        if row_width == self._row_width:
            return
        self._row_width = row_width
        if not self.active_prs:
            return
        highlighted = option_list.highlighted
        option_list.clear_options()
        self._populate_list(option_list, self.active_prs, row_width)
        if highlighted is not None and highlighted < len(self.active_prs):
            option_list.highlighted = highlighted

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
