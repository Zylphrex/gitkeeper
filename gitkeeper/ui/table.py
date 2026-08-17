from typing import List
from rich.console import Console
from rich.table import Table
from gitkeeper.scoring.pipeline import ScoredPullRequest


def render_pull_requests_table(
    scored_prs: List[ScoredPullRequest],
    min_threshold: int = 40,
    show_all: bool = False,
    console: Console = None,
) -> None:
    if console is None:
        console = Console()

    actionable_prs = [item for item in scored_prs if item.is_actionable]
    hidden_ambient_count = sum(1 for item in actionable_prs if item.score.total_score < min_threshold)

    displayed_prs = actionable_prs
    if not show_all:
        displayed_prs = [item for item in actionable_prs if item.score.total_score >= min_threshold]

    if not displayed_prs:
        if hidden_ambient_count > 0:
            console.print(f"[yellow]No high-priority reviews found ({hidden_ambient_count} ambient PRs hidden below threshold {min_threshold}). Use --all to view.[/yellow]")
        else:
            console.print("[green]✓ No pending pull request reviews found. You're all caught up![/green]")
        return

    table = Table(
        title="Ready For Your Review",
        show_header=True,
        header_style="bold cyan",
        title_style="bold",
        expand=True,
    )

    table.add_column("Score", justify="right", style="bold", no_wrap=True)
    table.add_column("PR", style="cyan", no_wrap=True)
    table.add_column("Repository", style="magenta")
    table.add_column("Author", style="blue", no_wrap=True)
    table.add_column("Title", style="white")
    table.add_column("Why", style="dim")

    for item in displayed_prs:
        pr = item.pr
        score = item.score.total_score

        # Color-code scores
        if score >= 75:
            score_str = f"[bold green]{score}[/bold green]"
        elif score >= 50:
            score_str = f"[bold yellow]{score}[/bold yellow]"
        else:
            score_str = f"[bold white]{score}[/bold white]"

        pr_link = f"#{pr.number}"
        repo_name = pr.repo_name_with_owner
        author_name = f"@{pr.author}"
        rationale = item.score.rationale

        table.add_row(
            score_str,
            pr_link,
            repo_name,
            author_name,
            pr.title,
            rationale,
        )

    console.print(table)

    if not show_all and hidden_ambient_count > 0:
        console.print(f"[dim]({hidden_ambient_count} ambient / low-relevance review requests hidden. Use --all to view all)[/dim]\n")
