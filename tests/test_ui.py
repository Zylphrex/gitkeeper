from datetime import datetime
from io import StringIO
import re
import pytest
from typing import Optional
from rich.console import Console
from textual.app import App, ComposeResult
from textual.widgets import Input, OptionList
from gitkeeper.config import Config
from gitkeeper.diff.parser import UnifiedDiffParser
from gitkeeper.github.client import (
    DraftReviewComment,
    PullRequestData,
    ReviewRecord,
    ReviewerRequest,
)
from gitkeeper.scoring.calculator import ScoreBreakdown, TriageTier
from gitkeeper.scoring.pipeline import ScoredPullRequest
from gitkeeper.ui.app import GitkeeperApp
from gitkeeper.ui.diff_view import DiffViewer, PRDiffView
from gitkeeper.ui.header import AppHeader
from gitkeeper.ui.list_view import PRListView
from gitkeeper.ui.modals import InlineCommentModal, SubmitReviewModal
from gitkeeper.ui.overview_view import PROverviewView


def _make_mock_scored_pr(number: int = 101, tier: TriageTier = TriageTier.T1) -> ScoredPullRequest:
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
        tier=tier,
        affinity_points=50.0,
        rationale="Author teammate",
    )
    return ScoredPullRequest(pr=pr, is_actionable=True, score=score)


LONG_PR_TITLE = (
    "fix: restore the consistent deduplication of dependency "
    "bundles during the IPFS ingestion warm-up sweep"
)


def _make_mock_scored_pr_with_metadata() -> ScoredPullRequest:
    pr = PullRequestData(
        id="PR_101",
        number=101,
        title=LONG_PR_TITLE,
        body="## Changes\n- Added OAuth2 JWT flow",
        url="https://github.com/acme/backend/pull/101",
        repo_name_with_owner="acme/backend",
        author="alice",
        is_draft=True,
        state="OPEN",
        created_at="2026-08-01T12:00:00Z",
        updated_at="2026-08-17T09:12:00Z",
        additions=134,
        deletions=23,
        changed_files_count=7,
        ci_status="SUCCESS",
        base_ref="main",
        head_ref="fix/ipfs-dedupe",
        requested_reviewers=[
            ReviewerRequest("core-team", is_team=True),
            ReviewerRequest("bob", is_team=False),
            ReviewerRequest("sam", is_team=False),
            ReviewerRequest("lea", is_team=False),
        ],
        reviews=[
            ReviewRecord("bob", "APPROVED", None),
            ReviewRecord("sam", "APPROVED", None),
            ReviewRecord("lea", "CHANGES_REQUESTED", None),
        ],
    )
    score = ScoreBreakdown(
        tier=TriageTier.T1,
        affinity_points=24.0,
        rationale="You touched 3 of 7 files recently; CI is green.",
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
            _make_mock_scored_pr(102, TriageTier.T2),
            _make_mock_scored_pr(101, TriageTier.T0),
            _make_mock_scored_pr(103, TriageTier.T1),
        ],
    )

    async with app.run_test() as pilot:
        # Check initial widgets
        pr_list = app.query_one("#pr-list-view", PRListView)
        # All 3 actionable PRs should be in active_prs sorted by tier (T0 first)
        assert len(pr_list.active_prs) == 3
        assert [p.pr.number for p in pr_list.active_prs] == [101, 103, 102]
        assert [p.score.tier for p in pr_list.active_prs] == [
            TriageTier.T0,
            TriageTier.T1,
            TriageTier.T2,
        ]

        overview = app.query_one("#pr-overview-view", PROverviewView)
        assert overview.scored_pr is not None
        assert overview.scored_pr.pr.number == 101

        # Test preserving selection across updates
        app._load_scored_prs([
            _make_mock_scored_pr(104, TriageTier.T0),
            _make_mock_scored_pr(101, TriageTier.T1),
            _make_mock_scored_pr(105, TriageTier.T2),
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
        scored_prs=[_make_mock_scored_pr(101, TriageTier.T0)],
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


def _make_mock_scored_pr_with_title(number: int, tier: TriageTier, title: str) -> ScoredPullRequest:
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
        tier=tier,
        affinity_points=50.0,
        rationale="Author teammate",
    )
    return ScoredPullRequest(pr=pr, is_actionable=True, score=score)


@pytest.mark.asyncio
async def test_vim_jk_moves_pr_list():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[
            _make_mock_scored_pr(102, TriageTier.T2),
            _make_mock_scored_pr(101, TriageTier.T0),
            _make_mock_scored_pr(103, TriageTier.T1),
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
            _make_mock_scored_pr(102, TriageTier.T3),
            _make_mock_scored_pr(101, TriageTier.T0),
            _make_mock_scored_pr(103, TriageTier.T2),
            _make_mock_scored_pr(104, TriageTier.T1),
            _make_mock_scored_pr(105, TriageTier.T3),
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
            _make_mock_scored_pr(102, TriageTier.T1),
            _make_mock_scored_pr(101, TriageTier.T0),
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
            _make_mock_scored_pr(102, TriageTier.T2),
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
async def test_arrow_up_down_moves_pr_list():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[
            _make_mock_scored_pr(102, TriageTier.T2),
            _make_mock_scored_pr(101, TriageTier.T0),
            _make_mock_scored_pr(103, TriageTier.T1),
        ],
    )
    async with app.run_test() as pilot:
        pr_list = app.query_one("#pr-option-list", OptionList)
        pr_list.focus()
        await pilot.pause()
        assert pr_list.highlighted == 0

        await pilot.press("down")
        await pilot.pause()
        assert pr_list.highlighted == 1

        await pilot.press("down")
        await pilot.pause()
        assert pr_list.highlighted == 2

        await pilot.press("up")
        await pilot.pause()
        assert pr_list.highlighted == 1


@pytest.mark.asyncio
async def test_arrow_left_right_focus_movement():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[
            _make_mock_scored_pr(102, TriageTier.T1),
            _make_mock_scored_pr(101, TriageTier.T0),
        ],
    )
    async with app.run_test() as pilot:
        app.action_tab_diff()
        diff_view = app.query_one("#pr-diff-view", PRDiffView)
        diff_view.load_diff(SAMPLE_MULTI_DIFF)

        pr_list = app.query_one("#pr-option-list", OptionList)
        pr_list.focus()
        await pilot.pause()

        await pilot.press("right")
        await pilot.pause()
        file_list = app.query_one("#file-option-list", OptionList)
        assert app.focused is file_list

        await pilot.press("right")
        await pilot.pause()
        diff_options = app.query_one("#diff-options", OptionList)
        assert app.focused is diff_options

        await pilot.press("left")
        await pilot.pause()
        assert app.focused is file_list

        await pilot.press("left")
        await pilot.pause()
        assert app.focused is pr_list


@pytest.mark.asyncio
async def test_arrow_left_right_boundary():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[
            _make_mock_scored_pr(102, TriageTier.T2),
        ],
    )
    async with app.run_test() as pilot:
        pr_list = app.query_one("#pr-option-list", OptionList)
        pr_list.focus()
        await pilot.pause()

        await pilot.press("left")
        await pilot.pause()
        assert app.focused is pr_list

        app.action_tab_diff()
        diff_view = app.query_one("#pr-diff-view", PRDiffView)
        diff_view.load_diff(SAMPLE_MULTI_DIFF)
        diff_options = app.query_one("#diff-options", OptionList)
        diff_options.focus()
        await pilot.pause()

        await pilot.press("right")
        await pilot.pause()
        assert app.focused is diff_options


@pytest.mark.asyncio
async def test_arrow_keys_move_cursor_in_modal():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[_make_mock_scored_pr(101, TriageTier.T0)],
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

        text_area.insert("ab")
        assert text_area.cursor_location[1] == 2
        await pilot.press("left")
        await pilot.pause()
        assert text_area.cursor_location[1] == 1
        assert app.focused is text_area
        assert pr_list.highlighted == 0


@pytest.mark.asyncio
async def test_vim_search_pr_list():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[
            _make_mock_scored_pr_with_title(101, TriageTier.T0, "OAuth2 implementation"),
            _make_mock_scored_pr_with_title(102, TriageTier.T1, "Fix database migration"),
            _make_mock_scored_pr_with_title(103, TriageTier.T0, "Update OAuth2 docs"),
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
            _make_mock_scored_pr_with_title(101, TriageTier.T0, "Alpha feature"),
            _make_mock_scored_pr_with_title(102, TriageTier.T1, "Beta release"),
            _make_mock_scored_pr_with_title(103, TriageTier.T2, "Alpha refactor"),
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
            _make_mock_scored_pr_with_title(101, TriageTier.T0, "OAuth2 implementation"),
            _make_mock_scored_pr_with_title(102, TriageTier.T1, "Fix database migration"),
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
        scored_prs=[_make_mock_scored_pr(101, TriageTier.T0)],
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
        scored_prs=[_make_mock_scored_pr(101, TriageTier.T0)],
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


class _OverviewOnlyApp(App):
    def __init__(self, scored_pr: ScoredPullRequest, **kwargs):
        super().__init__(**kwargs)
        self._scored_pr = scored_pr
        self.overview: Optional[PROverviewView] = None

    def compose(self) -> ComposeResult:
        self.overview = PROverviewView(id="pr-overview-view")
        yield self.overview

    def on_mount(self) -> None:
        self.overview.update_pr(self._scored_pr)


def _render_app_to_text(app: App) -> str:
    width, height = app.size
    buf = StringIO()
    console = Console(
        width=width,
        height=height,
        file=buf,
        force_terminal=False,
        color_system=None,
        legacy_windows=False,
    )
    renderable = app.screen._compositor.render_update(
        full=True, screen_stack=app._background_screens
    )
    console.print(renderable)
    # Strip border/padding decoration cells, then collapse whitespace so words
    # that wrap across rendered rows also match contiguous substrings.
    plain = buf.getvalue().translate(str.maketrans("", "", "│█"))
    return re.sub(r"\s+", " ", plain)


@pytest.mark.asyncio
async def test_pr_overview_metadata_wraps_in_panel():
    scored = _make_mock_scored_pr_with_metadata()
    app = _OverviewOnlyApp(scored)
    async with app.run_test(size=(44, 40)) as pilot:
        await pilot.pause()
        rendered = _render_app_to_text(app)

    overview = app.overview
    assert overview.scored_pr is scored

    # The full title is present across wrapped lines inside the panel (not clipped).
    assert LONG_PR_TITLE in rendered.replace("\n", " ")

    # All enriched metadata rows are rendered and are readable on-screen.
    for fragment in [
        "Repo: acme/backend",
        "Author: @alice",
        "base: main",
        "head: fix/ipfs-dedupe",
        "CI: SUCCESS",
        "+134",
        "-23",
        "files: 7",
        "Created: 2026-08-01",
        "Updated: 1d ago",
        "Reviewers:",
        "@bob",
        "+1 more",
        "2 ✓ · 1 ✗",
    ]:
        assert fragment in rendered, f"missing metadata fragment: {fragment!r}"


@pytest.mark.asyncio
async def test_pr_overview_placeholder_when_no_selection():
    app = _OverviewOnlyApp(None)
    async with app.run_test(size=(44, 20)) as pilot:
        await pilot.pause()
        rendered = _render_app_to_text(app)

    assert "No pull request selected" in rendered
