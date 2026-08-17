from datetime import datetime
import pytest
from gitkeeper.config import Config
from gitkeeper.diff.parser import UnifiedDiffParser
from gitkeeper.github.client import DraftReviewComment, PullRequestData
from gitkeeper.scoring.calculator import ScoreBreakdown
from gitkeeper.scoring.pipeline import ScoredPullRequest
from gitkeeper.ui.app import GitkeeperApp
from gitkeeper.ui.diff_view import DiffViewer, PRDiffView
from gitkeeper.ui.header import AppHeader
from gitkeeper.ui.list_view import PRListView
from gitkeeper.ui.modals import InlineCommentModal, SubmitReviewModal
from gitkeeper.ui.overview_view import PROverviewView


def _make_mock_scored_pr(number: int = 101, score_val: int = 85) -> ScoredPullRequest:
    pr = PullRequestData(
        id=f"PR_{number}",
        number=number,
        title="Add OAuth2 support",
        body="## Changes\n- Added OAuth2 JWT flow",
        url=f"https://github.com/acme/backend/pull/{number}",
        repo_name_with_owner="acme/backend",
        author="alice",
        is_draft=False,
        state="OPEN",
        created_at="2026-08-14T10:00:00Z",
        updated_at="2026-08-15T12:00:00Z",
        additions=45,
        deletions=10,
        changed_files_count=2,
        ci_status="SUCCESS",
    )
    score = ScoreBreakdown(
        affinity_points=50.0,
        assignment_points=25.0,
        urgency_points=10.0,
        total_score=score_val,
        rationale="Author teammate",
    )
    return ScoredPullRequest(pr=pr, is_actionable=True, score=score)


SAMPLE_DIFF = """diff --git a/auth/jwt.py b/auth/jwt.py
--- a/auth/jwt.py
+++ b/auth/jwt.py
@@ -1,3 +1,4 @@
 def verify():
-    return False
+    # RS256
+    return True
"""


@pytest.mark.asyncio
async def test_pr_list_view_and_selection():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[_make_mock_scored_pr(101, 85), _make_mock_scored_pr(102, 30)],
    )

    async with app.run_test() as pilot:
        # Check initial widgets
        pr_list = app.query_one("#pr-list-view", PRListView)
        assert len(pr_list.active_prs) == 1
        assert len(pr_list.ambient_prs) == 1

        overview = app.query_one("#pr-overview-view", PROverviewView)
        assert overview.scored_pr is not None
        assert overview.scored_pr.pr.number == 101

        # Test preserving selection across updates
        app._load_scored_prs([
            _make_mock_scored_pr(103, 90),
            _make_mock_scored_pr(101, 80),
        ])
        assert overview.scored_pr.pr.number == 101



@pytest.mark.asyncio
async def test_pr_diff_view_and_inline_comment():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[_make_mock_scored_pr(101, 85)],
    )

    async with app.run_test() as pilot:
        # Switch to diff tab
        app.action_tab_diff()
        diff_view = app.query_one("#pr-diff-view", PRDiffView)
        drafts = [DraftReviewComment(path="auth/jwt.py", line=3, body="Test comment")]
        diff_view.load_diff(SAMPLE_DIFF, drafts)

        assert len(diff_view.file_diffs) == 1
        diff_viewer = app.query_one("#diff-viewer", DiffViewer)
        assert diff_viewer.file_diff is not None
        assert diff_viewer.file_diff.display_path == "auth/jwt.py"

        # Test diff loading state
        diff_view.show_loading("#101")
        assert len(diff_view.file_diffs) == 0

        # Test diff error state
        diff_view.show_error("Failed to fetch diff from GitHub")
        assert len(diff_view.file_diffs) == 0



@pytest.mark.asyncio
async def test_app_header_widget():
    header = AppHeader()
    assert header.status_text == "Ready"
    assert header.is_loading is False
    assert header._render_timestamp_text() == "Last refreshed: Never"

    header.set_loading("Fetching PRs...")
    assert header.is_loading is True
    assert header.status_text == "Fetching PRs..."
    assert header._render_status_text() == "⠋ Fetching PRs..."

    ts = datetime(2026, 8, 17, 14, 30, 0)
    header.set_idle("Queue updated", refreshed_at=ts)
    assert header.is_loading is False
    assert header.status_text == "Queue updated"
    assert header._render_timestamp_text() == "Last refreshed: 14:30:00"

    header.set_error("Network timeout")
    assert header.is_loading is False
    assert header.status_text == "⚠ Network timeout"
    assert header._render_status_text() == "⚠ Network timeout"


@pytest.mark.asyncio
async def test_modals_interaction():
    # Test InlineCommentModal
    comment_modal = InlineCommentModal("auth/jwt.py", 10, "initial")
    # Test SubmitReviewModal
    review_modal = SubmitReviewModal("Test PR Title", 2)
    assert review_modal.pending_comments_count == 2
