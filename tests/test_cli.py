import pytest
from typer.testing import CliRunner
from gitkeeper.cli import app, PLAIN_BANNER
from gitkeeper.ui.app import GitkeeperApp


runner = CliRunner()


def test_cli_missing_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    result = runner.invoke(app, ["--config", "/nonexistent/path.yaml"])
    assert result.exit_code == 1
    assert "GitHub token not configured" in result.output


def test_cli_launches_tui(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "dummy_token")

    called_run = []

    def mock_run(self):
        called_run.append(True)

    monkeypatch.setattr(GitkeeperApp, "run", mock_run)

    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert len(called_run) == 1


def test_cli_help_shows_banner(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    first_banner_line = PLAIN_BANNER.splitlines()[0].strip()
    assert first_banner_line in result.output
    assert result.output.index(first_banner_line) < result.output.index("Usage:")


def test_cli_help_with_config_does_not_launch_tui(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    called_run = []

    def mock_run(self):
        called_run.append(True)

    monkeypatch.setattr(GitkeeperApp, "run", mock_run)

    result = runner.invoke(app, ["--config", "/nonexistent/path.yaml", "--help"])
    assert result.exit_code == 0
    assert PLAIN_BANNER.splitlines()[0].strip() in result.output
    assert len(called_run) == 0


def test_cli_help_omits_completion_options(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "--config" in result.output
    assert "--help" in result.output
    assert "--install-completion" not in result.output
    assert "--show-completion" not in result.output
