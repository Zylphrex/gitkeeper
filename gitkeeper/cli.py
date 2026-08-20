import os
import re
import sys
from pathlib import Path
from typing import Optional
import typer
import typer.rich_utils as typer_rich_utils
from rich.console import Console
from rich.text import Text
from typer.main import TyperGroup

from gitkeeper.config import load_config
from gitkeeper.github.auth import PersonalAccessTokenProvider
from gitkeeper.github.client import GitHubGraphQLClient
from gitkeeper.ui.app import GitkeeperApp

_LOGO_LINES = (
    "\x1b[0;37;40m \x1b[0;97;40m▄▀▀▀▀\x1b[0;37;40m▄   \x1b[0;97;40m█▀▀\x1b[0;37;40m█  \x1b[0;97;40m▄▀▀▀▀\x1b[0;37;40m▀█ \x1b[0;97;40m█▀▀\x1b[0;37;40m█ \x1b[0;97;40m▀\x1b[0;37;40m▀█  \x1b[0;97;40m▄▀▀▀▀\x1b[0;37;40m▀█  \x1b[0;97;40m▄▀▀▀▀\x1b[0;37;40m▀█ \x1b[0;97;40m█▀▀▀▀▀\x1b[0;37;40m▄   \x1b[0;97;40m▄▀▀▀▀\x1b[0;37;40m▀█ \x1b[0;97;40m█▀▀▀▀▀\x1b[0;37;40m▄ \x1b[0m",
    "\x1b[0;97;40m█\x1b[0;37;40m      █  \x1b[0;97;40m█\x1b[0;37;40m  \x1b[0;90;47m░\x1b[0;37;40m \x1b[0;97;40m█\x1b[0;37;40m      ▓ \x1b[0;97;40m█\x1b[0;37;40m  ▓   █ \x1b[0;97;40m█\x1b[0;37;40m      ▓ \x1b[0;97;40m█\x1b[0;37;40m      ▓ \x1b[0;97;40m█\x1b[0;37;40m      █ \x1b[0;97;40m█\x1b[0;37;40m      ▓ \x1b[0;97;40m█\x1b[0;37;40m      █\x1b[0m",
    "\x1b[0;97;40m█\x1b[0;37;40m  \x1b[0;97;40m█\x1b[0;97;47m▀\x1b[0;37;40m  \x1b[0;90;40m█\x1b[0;37;40m  \x1b[0;97;40m█\x1b[0;37;40m  \x1b[0;90;47m▒\x1b[0;37;40m \x1b[0;97;40m█\x1b[0;37;40m  \x1b[0;97;40m█▀\x1b[0;37;40m▀▀\x1b[0;90;40m▀\x1b[0;37;40m \x1b[0;97;40m█\x1b[0;37;40m   \x1b[0;90;40m▄\x1b[0;37;40m▄▀  \x1b[0;97;40m█\x1b[0;37;40m  \x1b[0;97;40m█\x1b[0;97;47m▀\x1b[0;90;47m▀\x1b[0;90;40m▀▀\x1b[0;37;40m \x1b[0;97;40m█\x1b[0;37;40m  \x1b[0;97;40m█\x1b[0;97;47m▀\x1b[0;90;47m▀\x1b[0;90;40m▀▀\x1b[0;37;40m \x1b[0;97;40m█\x1b[0;37;40m  \x1b[0;97;40m█\x1b[0;97;47m▀\x1b[0;37;40m  \x1b[0;90;40m█\x1b[0;37;40m \x1b[0;97;40m█\x1b[0;37;40m  \x1b[0;97;40m█\x1b[0;97;47m▀\x1b[0;90;47m▀\x1b[0;90;40m▀▀\x1b[0;37;40m \x1b[0;97;40m█\x1b[0;37;40m  \x1b[0;97;40m█\x1b[0;97;47m▀\x1b[0;37;40m  \x1b[0;90;40m█\x1b[0m",
    "\x1b[0;97;40m▓\x1b[0;37;40m  █\x1b[0;90;47m▄\x1b[0;90;40m▀▀▀█\x1b[0;37;40m \x1b[0;97;40m▓\x1b[0;37;40m  \x1b[0;90;47m▓\x1b[0;37;40m \x1b[0;97;40m▓\x1b[0;37;40m  █     \x1b[0;97;40m▓\x1b[0;37;40m  \x1b[0;90;40m▄\x1b[0;37;40m  \x1b[0;90;40m▀▄\x1b[0;37;40m \x1b[0;97;40m▓\x1b[0;37;40m  █\x1b[0;90;47m▄\x1b[0;90;40m█▄▄\x1b[0;37;40m \x1b[0;97;40m▓\x1b[0;37;40m  █\x1b[0;90;47m▄\x1b[0;90;40m█▄▄\x1b[0;37;40m \x1b[0;97;40m▓\x1b[0;37;40m  ▀\x1b[0;90;40m▀\x1b[0;37;40m \x1b[0;90;40m▄▀\x1b[0;37;40m \x1b[0;97;40m▓\x1b[0;37;40m  █\x1b[0;90;47m▄\x1b[0;90;40m█▄▄\x1b[0;37;40m \x1b[0;97;40m▓\x1b[0;37;40m  ▀\x1b[0;90;40m▀\x1b[0;37;40m \x1b[0;90;40m▀▄\x1b[0m",
    "\x1b[0;97;40m▒\x1b[0;37;40m  \x1b[0;90;40m▀▀\x1b[0;37;40m  \x1b[0;90;40m▓▀\x1b[0;37;40m \x1b[0;97;40m▒\x1b[0;37;40m  \x1b[0;90;40m█\x1b[0;37;40m \x1b[0;97;40m▒\x1b[0;37;40m  \x1b[0;90;47m▓\x1b[0;37;40m     \x1b[0;97;40m▒\x1b[0;37;40m  \x1b[0;90;40m█\x1b[0;37;40m   \x1b[0;90;40m▒\x1b[0;37;40m \x1b[0;97;40m▒\x1b[0;37;40m      \x1b[0;90;40m▒\x1b[0;37;40m \x1b[0;97;40m▒\x1b[0;37;40m      \x1b[0;90;40m▒\x1b[0;37;40m \x1b[0;97;40m▒\x1b[0;37;40m  \x1b[0;90;40m█▀▀\x1b[0;37;40m   \x1b[0;97;40m▒\x1b[0;37;40m      \x1b[0;90;40m▒\x1b[0;37;40m \x1b[0;97;40m▒\x1b[0;37;40m  \x1b[0;90;40m█\x1b[0;37;40m   \x1b[0;90;40m▒\x1b[0m",
    "\x1b[0;37;40m \x1b[0;90;40m▀▄▄▄▄▄█\x1b[0;37;40m  \x1b[0;97;40m░\x1b[0;90;40m▄▄█\x1b[0;37;40m \x1b[0;90;47m▓\x1b[0;90;40m▄▄█\x1b[0;37;40m     \x1b[0;97;40m░\x1b[0;90;40m▄▄█\x1b[0;37;40m \x1b[0;90;40m▄▄░\x1b[0;37;40m  \x1b[0;90;40m▀▄▄▄▄▄█\x1b[0;37;40m \x1b[0;90;40m▀▄▄▄▄▄█\x1b[0;37;40m \x1b[0;97;40m░\x1b[0;90;40m▄▄█\x1b[0;37;40m      \x1b[0;90;40m▀▄▄▄▄▄█\x1b[0;37;40m \x1b[0;97;40m░\x1b[0;90;40m▄▄█\x1b[0;37;40m \x1b[0;90;40m▄▄█\x1b[0m",
)

BANNER = "\n".join(
    line.replace(";40m", "m").replace(";47m", "m") for line in _LOGO_LINES
)

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

PLAIN_BANNER = _ANSI_RE.sub("", BANNER)


class BrandedTyperGroup(TyperGroup):
    """Typer group that prefixes help output with a logo banner."""

    def format_help(self, ctx, formatter):
        if self.rich_markup_mode is None:
            return super().format_help(ctx, formatter)
        Console().print(Text.from_ansi(BANNER))
        return typer_rich_utils.rich_format_help(
            obj=self, ctx=ctx, markup_mode=self.rich_markup_mode
        )


app = typer.Typer(
    cls=BrandedTyperGroup,
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
