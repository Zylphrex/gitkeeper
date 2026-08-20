"""Demo harness: run the gitkeeper TUI against a fully mock GitHub client.

Usage:
    .venv/bin/python demos/demo_gitkeeper.py

The app boots real, runs the normal refresh pipeline, and renders synthetic
PRs/diffs as if GitHub responded instantly (plus a little fake latency so the
recording shows the loading states).
"""

import time

from gitkeeper.config import Config
from gitkeeper.github.auth import PersonalAccessTokenProvider
from gitkeeper.github.client import (
    DraftReviewComment,
    GitHubGraphQLClient,
    PullRequestData,
    ReviewThread,
)
from gitkeeper.ui.app import GitkeeperApp

from mock_data import VIEWER, build_prs, build_threads, DIFFS


class MockGitHubClient(GitHubGraphQLClient):
    """In-memory stand-in for the GraphQL client; no network traffic."""

    def __init__(self, latency: bool = True) -> None:
        super().__init__(PersonalAccessTokenProvider("ghp_demo_token"))
        self._latency = latency

    def get_viewer_login(self) -> str:
        return VIEWER

    def fetch_pending_review_requests(
        self,
        username: str | None = None,
        include_authored: bool = False,
        include_reviewed: bool = False,
    ) -> list[PullRequestData]:
        if self._latency:
            time.sleep(2.4)  # let the "Fetching review requests…" state breathe
        return build_prs()

    def get_pull_request_diff(self, repo_name_with_owner: str, pull_number: int) -> str:
        if self._latency:
            time.sleep(1.1)
        return DIFFS.get(f"{repo_name_with_owner}#{pull_number}", "")

    def get_pull_request_review_threads(
        self, repo_name_with_owner: str, pull_number: int
    ) -> list[ReviewThread]:
        if self._latency:
            time.sleep(0.5)
        return build_threads().get(f"{repo_name_with_owner}#{pull_number}", [])

    def add_pull_request_review(
        self,
        pull_request_id: str,
        event: str,
        body: str | None = None,
        comments: list[DraftReviewComment] | None = None,
    ) -> dict:
        return {}


def main() -> None:
    config = Config()
    client = MockGitHubClient()
    GitkeeperApp(config=config, client=client).run()


if __name__ == "__main__":
    main()