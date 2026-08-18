import json

import httpx
import pytest
from gitkeeper.github.auth import PersonalAccessTokenProvider
from gitkeeper.github.client import DraftReviewComment, GitHubGraphQLClient


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
                        "body": "PR description markdown",
                        "url": "https://github.com/myorg/repo/pull/42",
                        "isDraft": False,
                        "state": "OPEN",
                        "baseRefName": "main",
                        "headRefName": "feature/auth-refactor",
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
                                {"commit": {"statusCheckRollup": {"state": "SUCCESS"}, "committedDate": "2026-08-16T11:30:00Z"}}
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
    assert pr.body == "PR description markdown"
    assert pr.author == "alice"
    assert pr.repo_name_with_owner == "myorg/repo"
    assert pr.is_draft is False
    assert pr.ci_status == "SUCCESS"
    assert pr.pushed_at == "2026-08-16T11:30:00Z"
    assert pr.base_ref == "main"
    assert pr.head_ref == "feature/auth-refactor"
    assert len(pr.requested_reviewers) == 2
    assert pr.requested_reviewers[0].login_or_slug == "octocat"
    assert pr.requested_reviewers[0].is_team is False
    assert pr.requested_reviewers[1].login_or_slug == "core-team"
    assert pr.requested_reviewers[1].is_team is True
    assert len(pr.files) == 2
    assert pr.files[0].path == "src/auth.py"


def test_fetch_pending_review_requests_paginates(monkeypatch):
    recorded_variables = []
    responses = [
        _search_payload(
            [_pr_node("PR_kwDO123", 42)],
            has_next_page=True,
            end_cursor="cursor-1",
        ),
        _search_payload([_pr_node("PR_kwDO456", 43)], has_next_page=False),
    ]
    _mock_httpx(monkeypatch, responses, recorded_variables)

    client = GitHubGraphQLClient(PersonalAccessTokenProvider("dummy_token"))
    prs = client.fetch_pending_review_requests("octocat")

    assert [pr.number for pr in prs] == [42, 43]
    assert len(recorded_variables) == 2
    assert recorded_variables[0].get("cursor") is None
    assert recorded_variables[1]["cursor"] == "cursor-1"


def test_fetch_pending_review_requests_stops_when_has_next_page_false(monkeypatch):
    recorded_variables = []
    responses = [_search_payload([_pr_node("PR_kwDO123", 42)], has_next_page=False)]
    _mock_httpx(monkeypatch, responses, recorded_variables)

    client = GitHubGraphQLClient(PersonalAccessTokenProvider("dummy_token"))
    prs = client.fetch_pending_review_requests("octocat")

    assert len(prs) == 1
    assert len(recorded_variables) == 1


def test_fetch_pending_review_requests_deduplicates_across_pages(monkeypatch):
    recorded_variables = []
    responses = [
        _search_payload(
            [_pr_node("PR_kwDO123", 42), _pr_node("PR_kwDO456", 43)],
            has_next_page=True,
            end_cursor="cursor-1",
        ),
        _search_payload(
            [_pr_node("PR_kwDO456", 43), _pr_node("PR_kwDO789", 44)],
            has_next_page=False,
        ),
    ]
    _mock_httpx(monkeypatch, responses, recorded_variables)

    client = GitHubGraphQLClient(PersonalAccessTokenProvider("dummy_token"))
    prs = client.fetch_pending_review_requests("octocat")

    assert [pr.number for pr in prs] == [42, 43, 44]
    assert len(prs) == 3


def _search_payload(
    nodes: list,
    has_next_page: bool = False,
    end_cursor: str | None = None,
) -> dict:
    page_info = {"hasNextPage": has_next_page}
    if end_cursor is not None:
        page_info["endCursor"] = end_cursor
    return {
        "data": {
            "search": {
                "issueCount": len(nodes),
                "pageInfo": page_info,
                "nodes": nodes,
            }
        }
    }


def _pr_node(node_id: str, number: int) -> dict:
    return {
        "id": node_id,
        "number": number,
        "title": f"PR {number}",
        "body": "",
        "url": f"https://github.com/myorg/repo/pull/{number}",
        "isDraft": False,
        "state": "OPEN",
        "baseRefName": "main",
        "headRefName": f"feature/{number}",
        "createdAt": "2026-08-15T10:00:00Z",
        "updatedAt": "2026-08-16T12:00:00Z",
        "additions": 1,
        "deletions": 0,
        "changedFiles": 1,
        "repository": {"nameWithOwner": "myorg/repo"},
        "author": {"login": "alice"},
        "reviewRequests": {"nodes": []},
        "reviews": {"nodes": []},
        "commits": {"nodes": []},
        "files": {"nodes": []},
    }


def _mock_httpx(monkeypatch, responses, recorded_variables=None):
    real_client = httpx.Client
    shared_responses = responses
    shared_variables = recorded_variables if recorded_variables is not None else []

    class ReconTransport(httpx.BaseTransport):
        def handle_request(self, request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content.decode("utf-8"))
            shared_variables.append(body.get("variables", {}))
            return httpx.Response(200, json=shared_responses.pop(0))

    def factory(**kwargs):
        return real_client(transport=ReconTransport())

    monkeypatch.setattr(httpx, "Client", factory)
    return shared_variables


def test_get_pull_request_diff(monkeypatch):
    sample_diff = "diff --git a/file.py b/file.py\n--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-old\n+new\n"

    class MockTransport(httpx.BaseTransport):
        def handle_request(self, request: httpx.Request) -> httpx.Response:
            assert request.headers.get("Accept") == "application/vnd.github.v3.diff"
            assert "repos/myorg/repo/pulls/42" in str(request.url)
            return httpx.Response(200, text=sample_diff)

    mock_client = httpx.Client(transport=MockTransport())
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client)

    client = GitHubGraphQLClient(PersonalAccessTokenProvider("dummy_token"))
    diff = client.get_pull_request_diff("myorg/repo", 42)
    assert diff == sample_diff


def test_add_pull_request_review_mutation(monkeypatch):
    recorded_requests = []

    class MockTransport(httpx.BaseTransport):
        def handle_request(self, request: httpx.Request) -> httpx.Response:
            import json
            payload = json.loads(request.content.decode("utf-8"))
            recorded_requests.append(payload)
            return httpx.Response(
                200,
                json={
                    "data": {
                        "addPullRequestReview": {
                            "pullRequestReview": {
                                "id": "PRR_kw123",
                                "state": "APPROVED",
                                "url": "https://github.com/myorg/repo/pull/42#pullrequestreview-123",
                            }
                        }
                    }
                },
            )

    mock_client = httpx.Client(transport=MockTransport())
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: mock_client)

    client = GitHubGraphQLClient(PersonalAccessTokenProvider("dummy_token"))
    comments = [DraftReviewComment(path="src/auth.py", line=15, body="Needs docstring")]
    result = client.add_pull_request_review(
        pull_request_id="PR_kwDO123",
        event="APPROVE",
        body="LGTM!",
        comments=comments,
    )

    assert result["addPullRequestReview"]["pullRequestReview"]["id"] == "PRR_kw123"
    assert len(recorded_requests) == 1
    input_vars = recorded_requests[0]["variables"]["input"]
    assert input_vars["pullRequestId"] == "PR_kwDO123"
    assert input_vars["event"] == "APPROVE"
    assert input_vars["body"] == "LGTM!"
    assert len(input_vars["threads"]) == 1
    assert input_vars["threads"][0]["path"] == "src/auth.py"
    assert input_vars["threads"][0]["line"] == 15
    assert input_vars["threads"][0]["body"] == "Needs docstring"
