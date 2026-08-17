import pytest
from typer.testing import CliRunner
from gitkeeper.cli import app
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
