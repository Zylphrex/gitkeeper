import json
from gitkeeper.github.client import GitHubGraphQLClient
from gitkeeper.github.auth import PersonalAccessTokenProvider
import pytest
from typer.testing import CliRunner
from gitkeeper.cli import app


runner = CliRunner()


def test_cli_missing_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    result = runner.invoke(app, ["queue", "--config", "/nonexistent/path.yaml"])
    assert result.exit_code == 1
    assert "GitHub token not configured" in result.output


def test_cli_queue_success(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "dummy_token")

    from gitkeeper.github.client import PullRequestData, PullRequestFile, ReviewerRequest

    mock_prs = [
        PullRequestData(
            id="PR_1",
            number=101,
            title="Add caching layer",
            url="https://github.com/org/repo/pull/101",
            repo_name_with_owner="org/repo",
            author="alice",
            is_draft=False,
            state="OPEN",
            created_at="2026-08-14T10:00:00Z",
            updated_at="2026-08-15T12:00:00Z",
            additions=30,
            deletions=5,
            changed_files_count=1,
            ci_status="SUCCESS",
            requested_reviewers=[ReviewerRequest(login_or_slug="octocat", is_team=False)],
            files=[PullRequestFile(path="cache.py", additions=30, deletions=5, change_type="MODIFIED")],
        )
    ]

    monkeypatch.setattr(GitHubGraphQLClient, "get_viewer_login", lambda self: "octocat")
    monkeypatch.setattr(GitHubGraphQLClient, "fetch_pending_review_requests", lambda self, user: mock_prs)

    result = runner.invoke(app, ["queue"])
    assert result.exit_code == 0
    assert "#101" in result.output
    assert "Add caching layer" in result.output
    assert "@alice" in result.output


def test_cli_queue_json(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "dummy_token")

    from gitkeeper.github.client import PullRequestData, PullRequestFile, ReviewerRequest

    mock_prs = [
        PullRequestData(
            id="PR_1",
            number=102,
            title="Fix memory leak",
            url="https://github.com/org/repo/pull/102",
            repo_name_with_owner="org/repo",
            author="bob",
            is_draft=False,
            state="OPEN",
            created_at="2026-08-14T10:00:00Z",
            updated_at="2026-08-15T12:00:00Z",
            additions=10,
            deletions=2,
            changed_files_count=1,
            ci_status="SUCCESS",
            requested_reviewers=[ReviewerRequest(login_or_slug="octocat", is_team=False)],
            files=[PullRequestFile(path="leak.py", additions=10, deletions=2, change_type="MODIFIED")],
        )
    ]

    monkeypatch.setattr(GitHubGraphQLClient, "get_viewer_login", lambda self: "octocat")
    monkeypatch.setattr(GitHubGraphQLClient, "fetch_pending_review_requests", lambda self, user: mock_prs)

    result = runner.invoke(app, ["queue", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["number"] == 102
    assert data[0]["author"] == "bob"
    assert data[0]["score"] > 0
