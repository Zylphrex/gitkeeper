from typing import Optional
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Label, Markdown

from gitkeeper.scoring.pipeline import ScoredPullRequest


class PROverviewView(Widget):
    """Displays metadata, scoring breakdown, and PR body markdown."""

    DEFAULT_CSS = """
    PROverviewView {
        height: 1fr;
        padding: 0 1;
    }

    #pr-meta-box {
        background: $panel;
        padding: 1;
        margin-bottom: 1;
        border-left: thick $primary;
    }

    #pr-title {
        text-style: bold;
    }

    #pr-meta-info {
        color: $text-muted;
    }

    #pr-score-box {
        background: $surface;
        padding: 1;
        margin-bottom: 1;
        border-left: thick $accent;
    }

    #pr-body-scroll {
        height: 1fr;
        border: solid $panel;
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scored_pr: Optional[ScoredPullRequest] = None

    def compose(self) -> ComposeResult:
        with Vertical(id="pr-meta-box"):
            yield Label("Select a PR from the queue", id="pr-title")
            yield Label("", id="pr-meta-info")

        with Vertical(id="pr-score-box"):
            yield Label("[bold]💡 Why this is relevant to you:[/bold]", id="pr-score-title")
            yield Label("", id="pr-score-rationale")
            yield Label("", id="pr-score-breakdown")

        with VerticalScroll(id="pr-body-scroll"):
            yield Markdown("", id="pr-body-markdown")

    def update_pr(self, scored_pr: Optional[ScoredPullRequest]) -> None:
        self.scored_pr = scored_pr
        title_label = self.query_one("#pr-title", Label)
        meta_label = self.query_one("#pr-meta-info", Label)
        rationale_label = self.query_one("#pr-score-rationale", Label)
        breakdown_label = self.query_one("#pr-score-breakdown", Label)
        markdown_view = self.query_one("#pr-body-markdown", Markdown)

        if not scored_pr:
            title_label.update("No pull request selected")
            meta_label.update("")
            rationale_label.update("")
            breakdown_label.update("")
            markdown_view.update("")
            return

        pr = scored_pr.pr
        score = scored_pr.score

        # Title and metadata
        ci_str = f" • CI: {pr.ci_status}" if pr.ci_status else ""
        draft_str = " [DRAFT]" if pr.is_draft else ""
        title_label.update(f"[bold cyan]#{pr.number}[/bold cyan] {pr.title}{draft_str}")
        meta_label.update(
            f"Repo: [magenta]{pr.repo_name_with_owner}[/magenta] | Author: [blue]@{pr.author}[/blue] | Changes: [green]+{pr.additions}[/green] / [red]-{pr.deletions}[/red]{ci_str}"
        )

        # Score rationale & points breakdown
        score_color = "green" if score.total_score >= 75 else ("yellow" if score.total_score >= 50 else "white")
        rationale_label.update(f"Score: [bold {score_color}]{score.total_score}[/bold {score_color}] — {score.rationale}")
        breakdown_label.update(
            f"[dim]Breakdown: Affinity: +{score.affinity_points} | Assignment: +{score.assignment_points} | Urgency: +{score.urgency_points}[/dim]"
        )

        # Markdown body
        body_content = pr.body if pr.body and pr.body.strip() else "_No description provided._"
        markdown_view.update(body_content)
