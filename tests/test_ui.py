from datetime import datetime
import pytest
from textual.widgets import Input, OptionList
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

SAMPLE_MULTI_DIFF = """diff --git a/auth/jwt.py b/auth/jwt.py
--- a/auth/jwt.py
+++ b/auth/jwt.py
@@ -1,3 +1,4 @@
 def verify():
-    return False
+    # RS256
+    return True
diff --git a/src/main.py b/src/main.py
--- a/src/main.py
+++ b/src/main.py
@@ -5,7 +5,7 @@
 def run():
-    old_code()
+    new_code()
diff --git a/tests/test_util.py b/tests/test_util.py
--- /dev/null
+++ b/tests/test_util.py
@@ -0,0 +1,5 @@
+def test_helper():
+    pass
"""


@pytest.mark.asyncio
async def test_pr_list_view_and_selection():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[
            _make_mock_scored_pr(102, 30),
            _make_mock_scored_pr(101, 85),
            _make_mock_scored_pr(103, 50),
        ],
    )

    async with app.run_test() as pilot:
        # Check initial widgets
        pr_list = app.query_one("#pr-list-view", PRListView)
        # All 3 actionable PRs should be in active_prs sorted strictly descending by score
        assert len(pr_list.active_prs) == 3
        assert [p.pr.number for p in pr_list.active_prs] == [101, 103, 102]
        assert [p.score.total_score for p in pr_list.active_prs] == [85, 50, 30]

        overview = app.query_one("#pr-overview-view", PROverviewView)
        assert overview.scored_pr is not None
        assert overview.scored_pr.pr.number == 101

        # Test preserving selection across updates
        app._load_scored_prs([
            _make_mock_scored_pr(104, 90),
            _make_mock_scored_pr(101, 80),
            _make_mock_scored_pr(105, 20),
        ])
        assert overview.scored_pr.pr.number == 101
        assert [p.pr.number for p in pr_list.active_prs] == [104, 101, 105]

        # Test clicking / selecting an option in list
        option_list = app.query_one("#pr-option-list", OptionList)
        option_list.action_first()
        option_list.action_select()
        await pilot.pause()
        assert overview.scored_pr.pr.number == 104

        # Test selecting last option in list
        option_list.action_last()
        option_list.action_select()
        await pilot.pause()
        # Check via synchronous state (the overview update is async)
        assert option_list.highlighted == 2
        assert pr_list.active_prs[option_list.highlighted].pr.number == 105



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
        assert diff_view.spinner_is_running is True

        # Test diff error state
        diff_view.show_error("Failed to fetch diff from GitHub")
        assert len(diff_view.file_diffs) == 0
        assert diff_view.spinner_is_running is False

        # Loading resolves and animation stops once the diff is loaded
        diff_view.show_loading("#101")
        assert diff_view.spinner_is_running is True
        diff_view.load_diff(SAMPLE_DIFF, drafts)
        assert len(diff_view.file_diffs) == 1
        assert diff_view.spinner_is_running is False



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

    # Frame animation cycles without waiting on a real timer (off-mount has no timer)
    header._spinner_tick()
    assert header._render_status_text() == "⠙ Fetching PRs..."
    header._spinner_tick()
    assert header._render_status_text() == "⠹ Fetching PRs..."

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


def _make_mock_scored_pr_with_title(number: int, score_val: int, title: str) -> ScoredPullRequest:
    pr = PullRequestData(
        id=f"PR_{number}",
        number=number,
        title=title,
        body="## Changes\n- Some changes",
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


@pytest.mark.asyncio
async def test_vim_jk_moves_pr_list():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[
            _make_mock_scored_pr(102, 30),
            _make_mock_scored_pr(101, 85),
            _make_mock_scored_pr(103, 50),
        ],
    )
    async with app.run_test() as pilot:
        pr_list = app.query_one("#pr-option-list", OptionList)
        pr_list.focus()
        await pilot.pause()
        assert pr_list.highlighted == 0

        await pilot.press("j")
        await pilot.pause()
        assert pr_list.highlighted == 1

        await pilot.press("j")
        await pilot.pause()
        assert pr_list.highlighted == 2

        await pilot.press("k")
        await pilot.pause()
        assert pr_list.highlighted == 1


@pytest.mark.asyncio
async def test_vim_gg_G_jumps_pr_list():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[
            _make_mock_scored_pr(102, 30),
            _make_mock_scored_pr(101, 85),
            _make_mock_scored_pr(103, 50),
            _make_mock_scored_pr(104, 70),
            _make_mock_scored_pr(105, 60),
        ],
    )
    async with app.run_test() as pilot:
        pr_list = app.query_one("#pr-option-list", OptionList)
        pr_list.focus()
        await pilot.pause()

        pr_list.highlighted = 2
        await pilot.press("g", "g")
        await pilot.pause()
        assert pr_list.highlighted == 0

        await pilot.press("G")
        await pilot.pause()
        assert pr_list.highlighted == 4


@pytest.mark.asyncio
async def test_vim_h_l_focus_movement():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[
            _make_mock_scored_pr(102, 30),
            _make_mock_scored_pr(101, 85),
        ],
    )
    async with app.run_test() as pilot:
        app.action_tab_diff()
        diff_view = app.query_one("#pr-diff-view", PRDiffView)
        diff_view.load_diff(SAMPLE_MULTI_DIFF)

        pr_list = app.query_one("#pr-option-list", OptionList)
        pr_list.focus()
        await pilot.pause()

        await pilot.press("l")
        await pilot.pause()
        file_list = app.query_one("#file-option-list", OptionList)
        assert app.focused is file_list

        await pilot.press("l")
        await pilot.pause()
        diff_options = app.query_one("#diff-options", OptionList)
        assert app.focused is diff_options

        await pilot.press("h")
        await pilot.pause()
        assert app.focused is file_list

        await pilot.press("h")
        await pilot.pause()
        assert app.focused is pr_list


@pytest.mark.asyncio
async def test_vim_h_l_boundary():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[
            _make_mock_scored_pr(102, 30),
        ],
    )
    async with app.run_test() as pilot:
        pr_list = app.query_one("#pr-option-list", OptionList)
        pr_list.focus()
        await pilot.pause()

        await pilot.press("h")
        await pilot.pause()
        assert app.focused is pr_list

        app.action_tab_diff()
        diff_view = app.query_one("#pr-diff-view", PRDiffView)
        diff_view.load_diff(SAMPLE_MULTI_DIFF)
        diff_options = app.query_one("#diff-options", OptionList)
        diff_options.focus()
        await pilot.pause()

        await pilot.press("l")
        await pilot.pause()
        assert app.focused is diff_options


@pytest.mark.asyncio
async def test_vim_search_pr_list():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[
            _make_mock_scored_pr_with_title(101, 85, "OAuth2 implementation"),
            _make_mock_scored_pr_with_title(102, 50, "Fix database migration"),
            _make_mock_scored_pr_with_title(103, 70, "Update OAuth2 docs"),
        ],
    )
    async with app.run_test() as pilot:
        pr_list_view = app.query_one("#pr-list-view", PRListView)
        option_list = app.query_one("#pr-option-list", OptionList)
        option_list.focus()
        await pilot.pause()

        assert len(pr_list_view.active_prs) == 3

        await pilot.press("/")
        await pilot.pause()
        search_input = app.query_one("#search-input", Input)
        assert search_input.has_class("-active")

        await pilot.press("O", "A", "u", "t", "h", "2")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        assert len(pr_list_view.active_prs) == 2
        assert pr_list_view.active_prs[0].pr.number == 101
        assert pr_list_view.active_prs[1].pr.number == 103


@pytest.mark.asyncio
async def test_vim_search_n_navigate():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[
            _make_mock_scored_pr_with_title(101, 85, "Alpha feature"),
            _make_mock_scored_pr_with_title(102, 50, "Beta release"),
            _make_mock_scored_pr_with_title(103, 70, "Alpha refactor"),
        ],
    )
    async with app.run_test() as pilot:
        pr_list_view = app.query_one("#pr-list-view", PRListView)
        option_list = app.query_one("#pr-option-list", OptionList)
        option_list.focus()
        await pilot.pause()

        await pilot.press("/")
        await pilot.pause()
        await pilot.press("A", "l", "p", "h", "a")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        assert len(pr_list_view.active_prs) == 2
        assert option_list.highlighted == 0

        await pilot.press("n")
        await pilot.pause()
        assert option_list.highlighted == 1

        await pilot.press("N")
        await pilot.pause()
        assert option_list.highlighted == 0


@pytest.mark.asyncio
async def test_vim_escape_clears_search():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[
            _make_mock_scored_pr_with_title(101, 85, "OAuth2 implementation"),
            _make_mock_scored_pr_with_title(102, 50, "Fix database migration"),
        ],
    )
    async with app.run_test() as pilot:
        pr_list_view = app.query_one("#pr-list-view", PRListView)
        option_list = app.query_one("#pr-option-list", OptionList)
        option_list.focus()
        await pilot.pause()

        await pilot.press("/")
        await pilot.pause()
        search_input = app.query_one("#search-input", Input)
        assert search_input.has_class("-active")

        await pilot.press("O", "A", "u", "t", "h")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert len(pr_list_view.active_prs) == 1

        await pilot.press("escape")
        await pilot.pause()
        assert len(pr_list_view.active_prs) == 2


@pytest.mark.asyncio
async def test_vim_escape_closes_modal():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[_make_mock_scored_pr(101, 85)],
    )
    async with app.run_test() as pilot:
        app.push_screen(InlineCommentModal("auth/jwt.py", 10))
        await pilot.pause()

        assert isinstance(app.screen, InlineCommentModal)

        await pilot.press("escape")
        await pilot.pause()

        assert not isinstance(app.screen, InlineCommentModal)


@pytest.mark.asyncio
async def test_vim_keys_do_not_fire_in_modal():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[_make_mock_scored_pr(101, 85)],
    )
    async with app.run_test() as pilot:
        pr_list = app.query_one("#pr-option-list", OptionList)
        pr_list.focus()
        await pilot.pause()
        assert pr_list.highlighted == 0

        app.push_screen(InlineCommentModal("auth/jwt.py", 10))
        await pilot.pause()

        text_area = app.screen.query_one("#comment-input")
        text_area.focus()
        await pilot.pause()

        await pilot.press("j", "k", "h", "l")
        await pilot.pause()

        assert "j" in text_area.text
        assert "k" in text_area.text
        assert pr_list.highlighted == 0
