import pytest
import httpx
from gitkeeper.github.auth import PersonalAccessTokenProvider
from gitkeeper.github.client import GitHubGraphQLClient


def test_personal_access_token_provider():
    provider = PersonalAccessTokenProvider("ghp_validtoken123")
    headers = provider.get_auth_headers()
    assert headers["Authorization"] == "Bearer ghp_validtoken123"
    assert headers["User-Agent"] == "gitkeeper-cli"

    with pytest.raises(ValueError):
        PersonalAccessTokenProvider("")


def test_github_graphql_client_fetch(monkeypatch):
    mock_response_payload = {
        "data": {
            "search": {
                "issueCount": 1,
                "nodes": [
                    {
                        "id": "PR_kwDO123",
                        "number": 42,
                        "title": "Refactor authentication flow",
                        "url": "https://github.com/myorg/repo/pull/42",
                        "isDraft": False,
                        "state": "OPEN",
                        "createdAt": "2026-08-15T10:00:00Z",
                        "updatedAt": "2026-08-16T12:00:00Z",
                        "additions": 45,
                        "deletions": 12,
                        "changedFiles": 2,
                        "repository": {"nameWithOwner": "myorg/repo"},
                        "author": {"login": "alice"},
                        "reviewRequests": {
                            "nodes": [
                                {"requestedReviewer": {"login": "octocat"}},
                                {"requestedReviewer": {"slug": "core-team"}},
                            ]
                        },
                        "reviews": {
                            "nodes": [
                                {"author": {"login": "bob"}, "state": "APPROVED", "submittedAt": "2026-08-15T12:00:00Z"}
                            ]
                        },
                        "commits": {
                            "nodes": [
                                {"commit": {"statusCheckRollup": {"state": "SUCCESS"}}}
                            ]
                        },
                        "files": {
                            "nodes": [
                                {"path": "src/auth.py", "additions": 40, "deletions": 10, "changeType": "MODIFIED"},
                                {"path": "tests/test_auth.py", "additions": 5, "deletions": 2, "changeType": "MODIFIED"},
                            ]
                        },
                    }
                ],
            }
        }
    }

    class MockTransport(httpx.BaseTransport):
        def handle_request(self, request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=mock_response_payload)

    mock_client = httpx.Client(transport=MockTransport())
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client)

    client = GitHubGraphQLClient(PersonalAccessTokenProvider("dummy_token"))
    prs = client.fetch_pending_review_requests("octocat")
    assert len(prs) == 1
    pr = prs[0]
    assert pr.number == 42
    assert pr.title == "Refactor authentication flow"
    assert pr.author == "alice"
    assert pr.repo_name_with_owner == "myorg/repo"
    assert pr.is_draft is False
    assert pr.ci_status == "SUCCESS"
    assert len(pr.requested_reviewers) == 2
    assert pr.requested_reviewers[0].login_or_slug == "octocat"
    assert pr.requested_reviewers[0].is_team is False
    assert pr.requested_reviewers[1].login_or_slug == "core-team"
    assert pr.requested_reviewers[1].is_team is True
    assert len(pr.files) == 2
    assert pr.files[0].path == "src/auth.py"
