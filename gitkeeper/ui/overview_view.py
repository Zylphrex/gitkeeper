from collections import Counter
from datetime import datetime, timezone
from typing import List, Optional

from textual.app import ComposeResult
from textual.containers import VerticalGroup, VerticalScroll
from textual.widget import Widget
from textual.widgets import Label, Markdown

from gitkeeper.github.client import ReviewRecord, ReviewerRequest
from gitkeeper.scoring.pipeline import ScoredPullRequest


def _ci_color(ci_status: Optional[str]) -> str:
    """Map a GitHub status-check rollup state to a rich color style."""
    color_by_state = {
        "SUCCESS": "green",
        "ERROR": "red",
        "FAILURE": "red",
        "PENDING": "yellow",
        "EXPECTED": "yellow",
    }
    return color_by_state.get(ci_status, "white")


def _relative_time(timestamp: Optional[str], now: Optional[datetime] = None) -> Optional[str]:
    """Render an ISO-8601 timestamp as a compact relative time like '2d ago'."""
    if not timestamp:
        return None
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    reference = now or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    seconds = max(0, int((reference - parsed).total_seconds()))
    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    if days < 7:
        return f"{days}d ago"
    weeks = days // 7
    if weeks < 5:
        return f"{weeks}w ago"
    return f"{days // 30}mo ago"


def _reviewer_label(reviewer: ReviewerRequest) -> str:
    """Render a single requested reviewer as text."""
    if reviewer.is_team:
        return reviewer.login_or_slug
    return f"@{reviewer.login_or_slug}"


def _reviewer_row(reviewers: List[ReviewerRequest]) -> Optional[str]:
    """Render the requested-reviewers row, capped at three names with a +N more suffix."""
    if not reviewers:
        return None
    names = [_reviewer_label(r) for r in reviewers[:3]]
    extra = len(reviewers) - 3
    if extra > 0:
        names.append(f"+{extra} more")
    return f"Reviewers: [dim]{', '.join(names)}[/dim]"


def _reviews_row(reviews: List[ReviewRecord]) -> Optional[str]:
    """Render existing reviews as a compact summary like '2 ✓ · 1 ✗'."""
    if not reviews:
        return None
    icons = {
        "APPROVED": "✓",
        "CHANGES_REQUESTED": "✗",
        "DISMISSED": "–",
    }
    counts = Counter(r.state for r in reviews)
    parts = [f"{count} {icons.get(state, state)}" for state, count in counts.items()]
    return f"Reviews: [dim]{' · '.join(parts)}[/dim]"


class PROverviewView(Widget):
    """Displays metadata, scoring breakdown, and PR body markdown."""

    DEFAULT_CSS = """
    PROverviewView {
        height: 1fr;
        width: 44;
        border-left: solid $primary;
        padding: 0 1;
    }

    #pr-meta-box {
        background: $panel;
        padding: 1;
        margin-bottom: 1;
        border-left: thick $primary;
        height: auto;
    }

    #pr-title {
        text-style: bold;
        width: 1fr;
    }

    #pr-meta-info {
        color: $text-muted;
        width: 1fr;
        text-overflow: ellipsis;
    }

    #pr-score-box {
        background: $surface;
        padding: 1;
        margin-bottom: 1;
        border-left: thick $accent;
        height: auto;
    }

    #pr-score-title {
        width: 1fr;
    }

    #pr-score-rationale {
        width: 1fr;
    }

    #pr-score-breakdown {
        width: 1fr;
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
        with VerticalGroup(id="pr-meta-box"):
            yield Label("Select a PR from the queue", id="pr-title")
            yield Label("", id="pr-meta-info")

        with VerticalGroup(id="pr-score-box"):
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

        draft_str = " [bold yellow][DRAFT][/bold yellow]" if pr.is_draft else ""
        title_label.update(f"[bold cyan]#{pr.number}[/bold cyan] {pr.title}{draft_str}")

        meta_rows = [
            f"Repo: [magenta]{pr.repo_name_with_owner}[/magenta] · "
            f"Author: [bold cyan]@{pr.author}[/bold cyan]"
        ]

        if pr.base_ref or pr.head_ref:
            base = pr.base_ref or "?"
            head = pr.head_ref or "?"
            meta_rows.append(f"base: [cyan]{base}[/cyan] ← head: [magenta]{head}[/magenta]")

        ci_color = _ci_color(pr.ci_status)
        meta_rows.append(
            f"CI: [{ci_color}]{pr.ci_status or '—'}[/{ci_color}] · "
            f"Δ: [green]+{pr.additions}[/green] / [red]-{pr.deletions}[/red] · "
            f"files: {pr.changed_files_count}"
        )

        dated_parts = []
        if pr.created_at:
            dated_parts.append(f"Created: {pr.created_at[:10]}")
        updated = _relative_time(pr.updated_at)
        if updated:
            dated_parts.append(f"Updated: {updated}")
        if dated_parts:
            meta_rows.append(" · ".join(dated_parts))

        reviewers = _reviewer_row(pr.requested_reviewers)
        if reviewers:
            meta_rows.append(reviewers)

        reviews = _reviews_row(pr.reviews)
        if reviews:
            meta_rows.append(reviews)

        meta_label.update("\n".join(meta_rows))

        score_color = "green" if score.total_score >= 75 else ("yellow" if score.total_score >= 50 else "white")
        rationale_label.update(f"Score: [bold {score_color}]{score.total_score}[/bold {score_color}] — {score.rationale}")
        breakdown_label.update(
            f"[dim]Breakdown: Affinity: +{score.affinity_points} | Assignment: +{score.assignment_points} | Urgency: +{score.urgency_points}[/dim]"
        )

        body_content = pr.body if pr.body and pr.body.strip() else "_No description provided._"
        markdown_view.update(body_content)