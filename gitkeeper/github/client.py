from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
import time
import httpx
from gitkeeper.github.auth import AuthProvider
from gitkeeper.github.queries import (
    PULL_REQUEST_THREADS_QUERY,
    REVIEW_REQUESTS_QUERY,
    VIEWER_QUERY,
)
from gitkeeper.github.mutations import ADD_PULL_REQUEST_REVIEW_MUTATION

RETRY_DELAYS = (1.0, 2.0)


@dataclass
class ReviewerRequest:
    login_or_slug: str
    is_team: bool


@dataclass
class ReviewRecord:
    author: str
    state: str
    submitted_at: Optional[str] = None


@dataclass
class PullRequestFile:
    path: str
    additions: int
    deletions: int
    change_type: str


@dataclass
class PullRequestData:
    id: str
    number: int
    title: str
    url: str
    repo_name_with_owner: str
    author: str
    is_draft: bool
    state: str
    created_at: str
    updated_at: str
    additions: int
    deletions: int
    changed_files_count: int
    ci_status: Optional[str]  # e.g., 'SUCCESS', 'FAILURE', 'PENDING', None
    pushed_at: Optional[str] = None  # latest commit committed date, ISO-8601
    base_ref: Optional[str] = None
    head_ref: Optional[str] = None
    body: str = ""
    requested_reviewers: List[ReviewerRequest] = field(default_factory=list)
    reviews: List[ReviewRecord] = field(default_factory=list)
    files: List[PullRequestFile] = field(default_factory=list)


@dataclass
class DraftReviewComment:
    path: str
    line: int
    body: str


@dataclass
class ThreadComment:
    author: str
    body: str


@dataclass
class ReviewThread:
    path: str
    line: Optional[int]
    comments: List[ThreadComment]


class GitHubGraphQLClient:
    PAGE_SIZE = 25
    MAX_RESULTS = 2000

    def __init__(
        self,
        auth_provider: AuthProvider,
        endpoint: str = "https://api.github.com/graphql",
        rest_endpoint: str = "https://api.github.com",
    ):
        self.auth_provider = auth_provider
        self.endpoint = endpoint
        self.rest_endpoint = rest_endpoint

    def _execute_query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        retries: bool = True,
    ) -> Dict[str, Any]:
        response = self._post_graphql(query, variables, retries=retries)
        if response.status_code == 401:
            raise PermissionError("Authentication failed: GitHub token is invalid or expired.")
        response.raise_for_status()
        data = response.json()

        if "errors" in data and data["errors"]:
            messages = [err.get("message", "Unknown GraphQL error") for err in data["errors"]]
            raise RuntimeError(f"GitHub GraphQL error: {'; '.join(messages)}")
        return data.get("data", {})

    def _request_with_retry(
        self,
        send: Callable[[], httpx.Response],
        retries: bool = True,
    ) -> httpx.Response:
        """Execute *send* once, retrying HTTP 5xx responses with backoff.

        Retries happen *only* on 5xx responses; 4xx errors and GraphQL-level
        errors in a 200 body are returned to the caller untouched.
        """
        max_retries = len(RETRY_DELAYS) if retries else 0
        for attempt in range(max_retries + 1):
            response = send()
            if response.status_code >= 500 and attempt < max_retries:
                time.sleep(RETRY_DELAYS[attempt])
                continue
            return response
        raise AssertionError("unreachable")

    def _post_graphql(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        retries: bool = True,
    ) -> httpx.Response:
        def send() -> httpx.Response:
            headers = self.auth_provider.get_auth_headers()
            with httpx.Client(timeout=15.0) as client:
                return client.post(
                    self.endpoint,
                    headers=headers,
                    json={"query": query, "variables": variables or {}},
                )

        return self._request_with_retry(send, retries=retries)

    def _get(
        self,
        url: str,
        headers: Dict[str, str],
        retries: bool = True,
    ) -> httpx.Response:
        def send() -> httpx.Response:
            with httpx.Client(timeout=30.0) as client:
                return client.get(url, headers=headers)

        return self._request_with_retry(send, retries=retries)

    def get_viewer_login(self) -> str:
        """Fetch current authenticated user's GitHub username."""
        data = self._execute_query(VIEWER_QUERY)
        return data.get("viewer", {}).get("login", "")

    def _search_all_nodes(self, query: str) -> List[Dict[str, Any]]:
        """Walk every page of *query* through the shared page-size/retry path."""
        seen_ids: set = set()
        all_nodes: List[Dict[str, Any]] = []
        cursor: Optional[str] = None

        while True:
            variables: Dict[str, Any] = {"query": query}
            if cursor:
                variables["cursor"] = cursor
            data = self._execute_query(REVIEW_REQUESTS_QUERY, variables)

            search = data.get("search", {})
            nodes = search.get("nodes", [])

            for node in nodes:
                node_id = node.get("id", "")
                if node_id in seen_ids:
                    continue
                seen_ids.add(node_id)
                all_nodes.append(node)

            page_info = search.get("pageInfo") or {}
            if not page_info.get("hasNextPage") or len(all_nodes) >= self.MAX_RESULTS:
                break
            cursor = page_info.get("endCursor")

        return all_nodes

    def fetch_pending_review_requests(
        self,
        username: Optional[str] = None,
        include_authored: bool = False,
    ) -> List[PullRequestData]:
        """
        Fetch open pull requests where review is requested from the user or
        their teams, plus (when *include_authored* is set) pull requests authored
        by the user. Search query format: `is:open is:pr review-requested:@me`
        (or `review-requested:USERNAME`) merged with `author:@me`.
        """
        user_filter = username if username else "@me"

        all_nodes: List[Dict[str, Any]] = []
        seen_ids: set = set()

        def extend_search(term: str) -> None:
            for node in self._search_all_nodes(term):
                node_id = node.get("id", "")
                if node_id in seen_ids:
                    continue
                seen_ids.add(node_id)
                all_nodes.append(node)

        extend_search(f"is:open is:pr review-requested:{user_filter} archived:false")
        if include_authored:
            extend_search(f"is:open is:pr author:{user_filter} archived:false")

        results: List[PullRequestData] = []

        for node in all_nodes:
            if not node or not isinstance(node, dict) or "number" not in node:
                continue

            repo_name = node.get("repository", {}).get("nameWithOwner", "")
            author_login = node.get("author", {}).get("login", "unknown") if node.get("author") else "unknown"

            # Parse requested reviewers
            requested: List[ReviewerRequest] = []
            for req in node.get("reviewRequests", {}).get("nodes", []):
                rev = req.get("requestedReviewer")
                if rev:
                    if "slug" in rev:
                        requested.append(ReviewerRequest(login_or_slug=rev["slug"], is_team=True))
                    elif "login" in rev:
                        requested.append(ReviewerRequest(login_or_slug=rev["login"], is_team=False))

            # Parse reviews
            reviews: List[ReviewRecord] = []
            for r in node.get("reviews", {}).get("nodes", []):
                rev_author = r.get("author", {}).get("login", "") if r.get("author") else ""
                reviews.append(
                    ReviewRecord(
                        author=rev_author,
                        state=r.get("state", ""),
                        submitted_at=r.get("submittedAt"),
                    )
                )

            # Parse status check rollup and latest push time
            ci_status = None
            pushed_at = None
            commits = node.get("commits", {}).get("nodes", [])
            if commits and commits[0].get("commit"):
                commit = commits[0]["commit"]
                rollup = commit.get("statusCheckRollup")
                if rollup:
                    ci_status = rollup.get("state")  # e.g., SUCCESS, FAILURE, PENDING, ERROR
                pushed_at = commit.get("committedDate")

            # Parse touched files
            files: List[PullRequestFile] = []
            for f in node.get("files", {}).get("nodes", []):
                files.append(
                    PullRequestFile(
                        path=f.get("path", ""),
                        additions=f.get("additions", 0),
                        deletions=f.get("deletions", 0),
                        change_type=f.get("changeType", "MODIFIED"),
                    )
                )

            results.append(
                PullRequestData(
                    id=node.get("id", ""),
                    number=node.get("number", 0),
                    title=node.get("title", ""),
                    body=node.get("body", "") or "",
                    url=node.get("url", ""),
                    repo_name_with_owner=repo_name,
                    author=author_login,
                    is_draft=node.get("isDraft", False),
                    state=node.get("state", "OPEN"),
                    created_at=node.get("createdAt", ""),
                    updated_at=node.get("updatedAt", ""),
                    additions=node.get("additions", 0),
                    deletions=node.get("deletions", 0),
                    changed_files_count=node.get("changedFiles", len(files)),
                    ci_status=ci_status,
                    pushed_at=pushed_at,
                    base_ref=node.get("baseRefName") or None,
                    head_ref=node.get("headRefName") or None,
                    requested_reviewers=requested,
                    reviews=reviews,
                    files=files,
                )
            )

        return results

    def get_pull_request_diff(self, repo_name_with_owner: str, pull_number: int) -> str:
        """Fetch unified diff text for a given pull request using GitHub REST API."""
        headers = self.auth_provider.get_auth_headers()
        headers["Accept"] = "application/vnd.github.v3.diff"
        url = f"{self.rest_endpoint}/repos/{repo_name_with_owner}/pulls/{pull_number}"

        response = self._get(url, headers, retries=True)
        if response.status_code == 401:
            raise PermissionError("Authentication failed: GitHub token is invalid or expired.")
        response.raise_for_status()
        return response.text

    def get_pull_request_review_threads(
        self, repo_name_with_owner: str, pull_number: int
    ) -> List[ReviewThread]:
        """Fetch inline review threads for a pull request, keyed by path and line."""
        owner, _, name = repo_name_with_owner.partition("/")
        data = self._execute_query(
            PULL_REQUEST_THREADS_QUERY,
            {"owner": owner, "name": name, "number": pull_number},
        )

        pull_request = data.get("repository", {}).get("pullRequest") or {}
        threads: List[ReviewThread] = []
        for node in pull_request.get("reviewThreads", {}).get("nodes", []):
            path = node.get("path")
            if not path:
                continue
            comments = [
                ThreadComment(
                    author=(c.get("author") or {}).get("login", ""),
                    body=c.get("body", ""),
                )
                for c in node.get("comments", {}).get("nodes", [])
            ]
            threads.append(ReviewThread(path=path, line=node.get("line"), comments=comments))
        return threads

    def add_pull_request_review(
        self,
        pull_request_id: str,
        event: str,  # 'APPROVE', 'REQUEST_CHANGES', 'COMMENT'
        body: Optional[str] = None,
        comments: Optional[List[DraftReviewComment]] = None,
    ) -> Dict[str, Any]:
        """Submit a pull request review mutation to GitHub GraphQL API."""
        input_data: Dict[str, Any] = {
            "pullRequestId": pull_request_id,
            "event": event,
        }
        if body is not None:
            input_data["body"] = body

        if comments:
            formatted_threads = []
            for c in comments:
                formatted_threads.append({
                    "path": c.path,
                    "line": c.line,
                    "body": c.body,
                })
            input_data["threads"] = formatted_threads

        return self._execute_query(
            ADD_PULL_REQUEST_REVIEW_MUTATION,
            {"input": input_data},
            retries=False,
        )
