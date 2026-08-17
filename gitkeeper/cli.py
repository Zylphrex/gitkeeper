import json
import os
import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

from gitkeeper.config import load_config
from gitkeeper.github.auth import PersonalAccessTokenProvider
from gitkeeper.github.client import GitHubGraphQLClient
from gitkeeper.repos import RepoLocator
from gitkeeper.scoring.pipeline import RelevancePipeline
from gitkeeper.ui.table import render_pull_requests_table

app = typer.Typer(help="Cuts through GitHub notification noise to find the PRs you're the right person to review.")
console = Console()


@app.command(name="queue")
@app.command(name="list")
def queue_command(
    config_path: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Path to config file (.gitkeeper.yaml)"
    ),
    threshold: Optional[int] = typer.Option(
        None, "--threshold", "-t", help="Minimum relevance score threshold"
    ),
    show_all: bool = typer.Option(
        False, "--all", "-a", help="Show all actionable PRs including those below threshold"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output results in raw JSON format"
    ),
):
    """List and rank pending pull requests requesting your review."""
    config = load_config(config_path)

    if not config.github.token:
        console.print("[red]Error:[/red] GitHub token not configured. Set GITHUB_TOKEN environment variable or configure in ~/.config/gitkeeper/config.yaml.")
        raise typer.Exit(code=1)

    min_threshold = threshold if threshold is not None else config.heuristics.min_score_threshold

    try:
        auth_provider = PersonalAccessTokenProvider(config.github.token)
        client = GitHubGraphQLClient(auth_provider)

        # Resolve username if not specified
        user = config.github.user
        if not user:
            try:
                user = client.get_viewer_login()
                config.github.user = user
            except Exception:
                pass

        with console.status("[bold green]Fetching review requests from GitHub..."):
            prs = client.fetch_pending_review_requests(user)

        repo_locator = RepoLocator(config.repositories)
        pipeline = RelevancePipeline(config, repo_locator)
        scored_prs = pipeline.process(prs)

        if json_output:
            out_data = []
            for item in scored_prs:
                if not show_all and item.is_actionable and item.score.total_score < min_threshold:
                    continue
                out_data.append({
                    "number": item.pr.number,
                    "title": item.pr.title,
                    "url": item.pr.url,
                    "repository": item.pr.repo_name_with_owner,
                    "author": item.pr.author,
                    "is_actionable": item.is_actionable,
                    "drop_reason": item.drop_reason,
                    "score": item.score.total_score,
                    "breakdown": {
                        "affinity": item.score.affinity_points,
                        "assignment": item.score.assignment_points,
                        "urgency": item.score.urgency_points,
                    },
                    "rationale": item.score.rationale,
                })
            typer.echo(json.dumps(out_data, indent=2))
            return

        render_pull_requests_table(
            scored_prs=scored_prs,
            min_threshold=min_threshold,
            show_all=show_all,
            console=console,
        )

    except PermissionError as e:
        console.print(f"[red]Authentication Error:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
