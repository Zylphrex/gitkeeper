import os
import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

from gitkeeper.config import load_config
from gitkeeper.github.auth import PersonalAccessTokenProvider
from gitkeeper.github.client import GitHubGraphQLClient
from gitkeeper.ui.app import GitkeeperApp

app = typer.Typer(
    help="Cuts through GitHub notification noise to find the PRs you're the right person to review.",
    invoke_without_command=True,
)
console = Console()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    config_path: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Path to config file (.gitkeeper.yaml)"
    ),
):
    """Launch the interactive PR review and triage terminal interface directly."""
    if ctx.invoked_subcommand is not None:
        return

    config = load_config(config_path)

    if not config.github.token:
        console.print(
            "[red]Error:[/red] GitHub token not configured. Set GITHUB_TOKEN environment variable or configure in ~/.config/gitkeeper/config.yaml."
        )
        raise typer.Exit(code=1)

    try:
        auth_provider = PersonalAccessTokenProvider(config.github.token)
        client = GitHubGraphQLClient(auth_provider)

        tui_app = GitkeeperApp(config=config, client=client)
        tui_app.run()

    except PermissionError as e:
        console.print(f"[red]Authentication Error:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
