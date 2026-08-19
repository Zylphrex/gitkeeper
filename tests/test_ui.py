from datetime import datetime
from io import StringIO
import asyncio
import re
import pytest
from typing import Optional
from rich.cells import cell_len
from rich.console import Console
from textual.app import App, ComposeResult
from textual.widgets import Button, Input, Label, Markdown, OptionList, TextArea
from gitkeeper.config import Config
from gitkeeper.diff.parser import UnifiedDiffParser
from gitkeeper.github.client import (
    DraftReviewComment,
    PullRequestData,
    ReviewRecord,
    ReviewThread,
    ReviewerRequest,
    ThreadComment,
)
from gitkeeper.scoring.calculator import ScoreBreakdown, TriageTier
from gitkeeper.scoring.pipeline import ScoredPullRequest
from gitkeeper.ui.app import GitkeeperApp
from gitkeeper.ui.diff_view import DiffViewer, PRDiffView
from gitkeeper.ui.header import AppHeader
from gitkeeper.ui.list_view import PRListView, ROW_WIDTH, _pr_number_text, _truncate
from gitkeeper.ui.modals import InlineCommentModal, SubmitReviewModal
from gitkeeper.ui.overview_view import PROverviewView


def _make_mock_scored_pr(
    number: int = 101, tier: TriageTier = TriageTier.T1
) -> ScoredPullRequest:
    return _make_mock_scored_pr_with_body(number, tier, "## Changes\n- Added OAuth2 JWT flow")


def _make_mock_scored_pr_with_body(
    number: int, tier: TriageTier, body: str
) -> ScoredPullRequest:
    pr = PullRequestData(
        id=f"PR_{number}",
        number=number,
        title=f"PR {number}",
        body=body,
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

WS_ONLY_DIFF = """diff --git a/auth/jwt.py b/auth/jwt.py
--- a/auth/jwt.py
+++ b/auth/jwt.py
@@ -1,3 +1,3 @@
 import re
-def foo()   
+def foo()
"""

WS_INTERLEAVED_DIFF = """diff --git a/auth/jwt.py b/auth/jwt.py
--- a/auth/jwt.py
+++ b/auth/jwt.py
@@ -1,5 +1,5 @@
 import re
-def foo()   
+def foo()
-    old_secret = SECRET
+    new_secret = NEW_SECRET
"""


def test_pr_number_text_hyperlink_with_url():
    console = Console()
    url = "https://github.com/acme/backend/pull/101"
    text = _pr_number_text(101, url)
    assert text.get_style_at_offset(console, 0).link == url
    assert str(text) == "#101 "


def test_pr_number_text_plain_without_url():
    console = Console()
    text = _pr_number_text(102, None)
    assert text.get_style_at_offset(console, 0).link is None
    text_blank = _pr_number_text(102, "")
    assert text_blank.get_style_at_offset(console, 0).link is None


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

        # Let the preserved-selection highlight event settle before acting.
        await pilot.pause()

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
async def test_pr_list_option_shows_author_without_reason_chip():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[_make_mock_scored_pr_with_metadata()],
    )
    async with app.run_test() as pilot:
        option_list = app.query_one("#pr-option-list", OptionList)
        option = option_list.get_option_at_index(0)
        lines = str(option.prompt).splitlines()

        assert len(lines) == 2
        # Author sits on the first row alongside the repo short name.
        assert "backend" in lines[0]
        assert "@alice" in lines[0]
        # No scoring-reason chip remains on the row.
        assert "(" not in str(option.prompt)


@pytest.mark.asyncio
async def test_pr_list_long_title_ellipsized_flush_left():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[_make_mock_scored_pr_with_metadata()],
    )
    async with app.run_test() as pilot:
        option_list = app.query_one("#pr-option-list", OptionList)
        option = option_list.get_option_at_index(0)
        lines = str(option.prompt).splitlines()

        # Title stays on its own single line: never wraps to a third row.
        assert len(lines) == 2
        title_line = lines[1]
        # Flush-left: no leading indent on the title line.
        assert title_line.startswith("fix: restore")
        # Truncated with a trailing ellipsis to the row width.
        assert title_line.endswith("…")
        assert len(title_line) == ROW_WIDTH
        assert "…" not in title_line[:-1]


@pytest.mark.asyncio
async def test_pr_list_short_title_untruncated():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[_make_mock_scored_pr(102, TriageTier.T2)],
    )
    async with app.run_test() as pilot:
        option_list = app.query_one("#pr-option-list", OptionList)
        option = option_list.get_option_at_index(0)
        lines = str(option.prompt).splitlines()

        assert lines[1] == "PR 102"
        assert "…" not in lines[1]
        assert len(lines) == 2


@pytest.mark.asyncio
async def test_pr_list_rows_shrink_when_window_is_narrow():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[_make_mock_scored_pr_with_metadata()],
    )
    async with app.run_test(size=(30, 40)) as pilot:
        await pilot.pause()
        option_list = app.query_one("#pr-option-list", OptionList)
        lines = str(option_list.get_option_at_index(0).prompt).splitlines()

        # Exactly two rows, author stays on line 1, title never wraps.
        assert len(lines) == 2
        assert "@alice" in lines[0]
        assert lines[1].endswith("…")
        assert len(lines[1]) <= ROW_WIDTH


@pytest.mark.asyncio
async def test_pr_list_rows_reflow_on_resize():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[_make_mock_scored_pr_with_metadata()],
    )
    async with app.run_test(size=(100, 40)) as pilot:
        await pilot.pause()
        option_list = app.query_one("#pr-option-list", OptionList)
        wide_length = len(str(option_list.get_option_at_index(0).prompt).splitlines()[1])

        await pilot.resize_terminal(30, 40)
        await pilot.pause()

        option_list = app.query_one("#pr-option-list", OptionList)
        lines = str(option_list.get_option_at_index(0).prompt).splitlines()
        assert len(lines) == 2
        assert "@alice" in lines[0]
        assert len(lines[1]) < wide_length
        assert lines[1].endswith("…")



def _make_mock_scored_pr_with_wide_metadata(number: int) -> ScoredPullRequest:
    pr = PullRequestData(
        id=f"PR_{number}",
        number=number,
        title=f"폭넓은 제목 {number} " + "가" * 40,
        body="## Changes\n- Added OAuth2 JWT flow",
        url=f"https://github.com/acme/backend/pull/{number}",
        repo_name_with_owner="acme/한국어-리포지토리-이름이-아주-깁니다",
        author="팀개발자아이디가무척길어요",
        is_draft=False,
        state="OPEN",
        created_at="2026-08-14T10:00:00Z",
        updated_at="2026-08-15T12:00:00Z",
        additions=10,
        deletions=5,
        changed_files_count=2,
        ci_status="SUCCESS",
    )
    score = ScoreBreakdown(
        tier=TriageTier.T1,
        affinity_points=30.0,
        rationale="Author teammate",
    )
    return ScoredPullRequest(pr=pr, is_actionable=True, score=score)


def _make_mock_scored_pr_long_repo(number: int) -> ScoredPullRequest:
    pr = PullRequestData(
        id=f"PR_{number}",
        number=number,
        title=LONG_PR_TITLE,
        body="## Changes\n- Added OAuth2 JWT flow",
        url=f"https://github.com/acme/backend/pull/{number}",
        repo_name_with_owner="acme/backend-services-platform-team-repo",
        author="alice",
        is_draft=False,
        state="OPEN",
        created_at="2026-08-14T10:00:00Z",
        updated_at="2026-08-15T12:00:00Z",
        additions=134,
        deletions=23,
        changed_files_count=7,
        ci_status="SUCCESS",
    )
    score = ScoreBreakdown(
        tier=TriageTier.T1,
        affinity_points=24.0,
        rationale="Author teammate",
    )
    return ScoredPullRequest(pr=pr, is_actionable=True, score=score)


@pytest.mark.asyncio
async def test_pr_list_entries_stay_two_rows_when_scrollable():
    # A queue taller than the pane forces the vertical scrollbar to show,
    # which steals columns from the option render width. Entries must stay
    # exactly two rows even then.
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[_make_mock_scored_pr_long_repo(1000 + i) for i in range(15)],
    )
    async with app.run_test(size=(100, 20)) as pilot:
        await pilot.pause()
        option_list = app.query_one("#pr-option-list", OptionList)

        # Proof the list is actually scrollable (scrollbar visible).
        assert option_list.virtual_size.height > option_list.content_region.height
        assert option_list.scrollable_content_region.width < option_list.content_region.width

        # Every entry is exactly two rows: metadata row + title row.
        assert option_list.virtual_size.height == 2 * option_list.option_count
        for idx in range(option_list.option_count):
            lines = str(option_list.get_option_at_index(idx).prompt).splitlines()
            assert len(lines) == 2, f"option {idx} wrapped to {len(lines)} rows"
            assert "@alice" in lines[0], f"option {idx}: author not on metadata row"
            assert lines[1].endswith("…"), f"option {idx}: title not truncated"


@pytest.mark.asyncio
async def test_pr_list_wide_glyphs_stay_two_rows():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[_make_mock_scored_pr_with_wide_metadata(101 + i) for i in range(3)],
    )
    async with app.run_test(size=(100, 24)) as pilot:
        await pilot.pause()
        option_list = app.query_one("#pr-option-list", OptionList)

        assert option_list.virtual_size.height == 2 * option_list.option_count
        render_width = option_list.content_region.width
        for idx in range(option_list.option_count):
            lines = str(option_list.get_option_at_index(idx).prompt).splitlines()
            assert len(lines) == 2, f"option {idx} wrapped to {len(lines)} rows"
            assert "@" in lines[0], f"option {idx}: author not on metadata row"
            assert cell_len(lines[0]) <= render_width, f"option {idx}: metadata row exceeds pane"
            assert cell_len(lines[1]) <= render_width, f"option {idx}: title row exceeds pane"


def test_truncate_measures_display_cells():
    assert _truncate("가나다라마바사", 6) == "가나…"
    assert _truncate("abcdefgh", 6) == "abcde…"
    assert _truncate("짧음", 10) == "짧음"
    assert _truncate("ascii", 10) == "ascii"


@pytest.mark.asyncio
async def test_pr_diff_view_and_inline_comment():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[_make_mock_scored_pr(101, TriageTier.T0)],
    )

    async with app.run_test() as pilot:
        diff_view = app.query_one("#pr-diff-view", PRDiffView)
        drafts = [DraftReviewComment(path="auth/jwt.py", line=3, body="Test comment")]
        diff_view.load_diff(SAMPLE_DIFF, draft_comments=drafts)

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
        diff_view.load_diff(SAMPLE_DIFF, draft_comments=drafts)
        assert len(diff_view.file_diffs) == 1
        assert diff_view.spinner_is_running is False



@pytest.mark.asyncio
async def test_file_list_renders_compact_tree():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[_make_mock_scored_pr(101, TriageTier.T0)],
    )
    async with app.run_test() as pilot:
        diff_view = app.query_one("#pr-diff-view", PRDiffView)
        diff_view.load_diff(SAMPLE_MULTI_DIFF)
        file_list = app.query_one("#file-option-list", OptionList)

        # auth/, src/, tests/: one header + one leaf each → 6 rows total.
        assert file_list.option_count == 6
        for idx in (0, 2, 4):
            assert file_list.get_option_at_index(idx).disabled, f"row {idx} should be a header"
        for idx in (1, 3, 5):
            assert not file_list.get_option_at_index(idx).disabled

        # First leaf (auth/jwt.py) is auto-selected.
        assert file_list.highlighted == 1
        diff_viewer = app.query_one("#diff-viewer", DiffViewer)
        assert diff_viewer.file_diff.display_path == "auth/jwt.py"

        # Cursor navigation skips header rows: down from row 1 lands on row 3.
        file_list.focus()
        await pilot.press("j")
        await pilot.pause()
        assert file_list.highlighted == 3
        assert diff_viewer.file_diff.display_path == "src/main.py"

        await pilot.press("j")
        await pilot.pause()
        assert file_list.highlighted == 5
        assert diff_viewer.file_diff.display_path == "tests/test_util.py"


@pytest.mark.asyncio
async def test_file_search_navigates_compact_tree():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[_make_mock_scored_pr(101, TriageTier.T0)],
    )
    async with app.run_test() as pilot:
        diff_view = app.query_one("#pr-diff-view", PRDiffView)
        diff_view.load_diff(SAMPLE_MULTI_DIFF)
        file_list = app.query_one("#file-option-list", OptionList)
        file_list.focus()
        await pilot.pause()

        await pilot.press("/")
        await pilot.pause()
        search_input = app.query_one("#search-input", Input)
        assert search_input.has_class("-active")

        # "t" matches auth/jwt.py and tests/test_util.py (not src/main.py).
        await pilot.press("t")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        assert [f.display_path for f in diff_view.file_diffs] == [
            "auth/jwt.py",
            "tests/test_util.py",
        ]
        # Two headers + two leaves; first match highlighted.
        assert file_list.highlighted == 1
        diff_viewer = app.query_one("#diff-viewer", DiffViewer)
        assert diff_viewer.file_diff.display_path == "auth/jwt.py"

        # n / N move between the two matched files.
        await pilot.press("n")
        await pilot.pause()
        assert file_list.highlighted == 3
        assert diff_viewer.file_diff.display_path == "tests/test_util.py"

        await pilot.press("N")
        await pilot.pause()
        assert file_list.highlighted == 1
        assert diff_viewer.file_diff.display_path == "auth/jwt.py"

        # Esc clears the filter and restores the full tree.
        await pilot.press("escape")
        await pilot.pause()
        assert len(diff_view.file_diffs) == 3
        assert file_list.option_count == 6
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


@pytest.mark.asyncio
async def test_comment_action_opens_modal_and_stores_draft():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[_make_mock_scored_pr(101, TriageTier.T0)],
    )
    async with app.run_test() as pilot:
        diff_view = app.query_one("#pr-diff-view", PRDiffView)
        diff_view.load_diff(SAMPLE_DIFF)
        await pilot.pause()  # drain the async file-list highlight re-render

        diff_options = app.query_one("#diff-options", OptionList)
        diff_options.focus()
        diff_options.highlighted = 3  # added line "    # RS256" → new line 2
        await pilot.pause()

        await pilot.press("c")
        await pilot.pause()

        assert isinstance(app.screen, InlineCommentModal)

        text_area = app.screen.query_one("#comment-input", TextArea)
        text_area.focus()
        text_area.text = "needs a docstring"
        await pilot.pause()

        app.screen.query_one("#btn-save", Button).press()
        await pilot.pause()

        pr_key = "acme/backend#101"
        assert pr_key in app.draft_comments
        draft = app.draft_comments[pr_key][0]
        assert isinstance(draft, DraftReviewComment)
        assert draft.path == "auth/jwt.py"
        assert draft.line == 2
        assert draft.body == "needs a docstring"

        assert not isinstance(app.screen, InlineCommentModal)


@pytest.mark.asyncio
async def test_saving_comment_preserves_diff_position():
    """Saving an inline comment must not reset the file tree or diff position."""
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[_make_mock_scored_pr(101, TriageTier.T0)],
    )
    async with app.run_test() as pilot:
        diff_view = app.query_one("#pr-diff-view", PRDiffView)
        diff_view.load_diff(SAMPLE_MULTI_DIFF)
        await pilot.pause()  # drain the async file-list highlight re-render

        file_list = app.query_one("#file-option-list", OptionList)
        # Select src/main.py: auth/ header(0), leaf(1), src/ header(2), leaf(3)
        file_list.highlighted = 3
        await pilot.pause()

        diff_options = app.query_one("#diff-options", OptionList)
        diff_options.focus()
        diff_options.highlighted = 3  # "+    new_code()" → new line 6
        await pilot.pause()

        file_before = file_list.highlighted
        line_before = diff_options.highlighted
        scroll_before = diff_options.scroll_offset

        await pilot.press("c")
        await pilot.pause()
        assert isinstance(app.screen, InlineCommentModal)

        text_area = app.screen.query_one("#comment-input", TextArea)
        text_area.focus()
        text_area.text = "needs a docstring"
        await pilot.pause()
        app.screen.query_one("#btn-save", Button).press()
        await pilot.pause()

        pr_key = "acme/backend#101"
        assert pr_key in app.draft_comments
        draft = app.draft_comments[pr_key][0]
        assert draft.path == "src/main.py"
        assert draft.line == 6
        assert not isinstance(app.screen, InlineCommentModal)

        # Position preserved after save
        assert file_list.highlighted == file_before
        assert diff_options.highlighted == line_before
        assert diff_options.scroll_offset == scroll_before
        assert app.focused is diff_options

        # Pending comment label is visible on the commented line
        prompt = diff_options.get_option_at_index(3).prompt
        assert "needs a docstring" in str(prompt)


@pytest.mark.asyncio
async def test_cancelling_comment_preserves_diff_position():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[_make_mock_scored_pr(101, TriageTier.T0)],
    )
    async with app.run_test() as pilot:
        diff_view = app.query_one("#pr-diff-view", PRDiffView)
        diff_view.load_diff(SAMPLE_MULTI_DIFF)
        await pilot.pause()

        file_list = app.query_one("#file-option-list", OptionList)
        file_list.highlighted = 3  # src/main.py
        await pilot.pause()

        diff_options = app.query_one("#diff-options", OptionList)
        diff_options.focus()
        diff_options.highlighted = 3
        await pilot.pause()

        file_before = file_list.highlighted
        line_before = diff_options.highlighted
        scroll_before = diff_options.scroll_offset

        await pilot.press("c")
        await pilot.pause()
        assert isinstance(app.screen, InlineCommentModal)

        await pilot.press("escape")
        await pilot.pause()

        assert not isinstance(app.screen, InlineCommentModal)
        assert "acme/backend#101" not in app.draft_comments
        assert file_list.highlighted == file_before
        assert diff_options.highlighted == line_before
        assert diff_options.scroll_offset == scroll_before
        assert app.focused is diff_options


@pytest.mark.asyncio
async def test_add_pending_comment_updates_only_target_row():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[_make_mock_scored_pr(101, TriageTier.T0)],
    )
    async with app.run_test() as pilot:
        diff_view = app.query_one("#pr-diff-view", PRDiffView)
        diff_view.load_diff(SAMPLE_DIFF)
        await pilot.pause()

        diff_options = app.query_one("#diff-options", OptionList)
        before = [str(diff_options.get_option_at_index(i).prompt) for i in range(diff_options.option_count)]

        diff_view.add_draft_comment("auth/jwt.py", 2, "please expand")

        assert diff_options.option_count == len(before)
        for i in range(diff_options.option_count):
            after = str(diff_options.get_option_at_index(i).prompt)
            if i in (2, 3):  # "-    return False" (old 2) and "+    # RS256" (new 2)
                assert "please expand" in after
            else:
                assert after == before[i]


@pytest.mark.asyncio
async def test_set_file_diff_renders_existing_threads_on_matching_lines():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[_make_mock_scored_pr(101, TriageTier.T0)],
    )
    async with app.run_test() as pilot:
        diff_view = app.query_one("#pr-diff-view", PRDiffView)
        threads = [
            ReviewThread(
                path="auth/jwt.py",
                line=2,
                comments=[
                    ThreadComment(author="alice", body="Add docs"),
                    ThreadComment(author="bob", body="Agreed"),
                ],
            ),
            # line 999 is not in the rendered diff and must be skipped
            ReviewThread(path="auth/jwt.py", line=999, comments=[ThreadComment(author="carol", body="Orphan")]),
            # a line-less thread (left-side/deleted thread) must be skipped
            ReviewThread(path="auth/jwt.py", line=None, comments=[ThreadComment(author="dave", body="Side")]),
            # a thread for another file must not leak here
            ReviewThread(path="other.py", line=2, comments=[ThreadComment(author="erin", body="Other file")]),
        ]
        diff_view.load_diff(SAMPLE_DIFF, existing_threads=threads)
        await pilot.pause()

        diff_options = app.query_one("#diff-options", OptionList)
        # SAMPLE_DIFF rows: 0=@@ hunk header 1=context(old1,new1) 2=delete(old2)
        # 3=add(new2) 4=add(new3); line 2 maps to rows 2 and 3.
        prompts = [str(diff_options.get_option_at_index(i).prompt) for i in range(diff_options.option_count)]
        assert len(prompts) == 5
        for i in (2, 3):
            assert "alice: Add docs" in prompts[i]
            assert "bob: Agreed" in prompts[i]
        for i in (0, 1, 4):
            assert "alice" not in prompts[i]
            assert "carol" not in prompts[i]
            assert "dave" not in prompts[i]
            assert "erin" not in prompts[i]


@pytest.mark.asyncio
async def test_existing_threads_and_pending_comment_render_distinctly():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[_make_mock_scored_pr(101, TriageTier.T0)],
    )
    async with app.run_test() as pilot:
        diff_view = app.query_one("#pr-diff-view", PRDiffView)
        diff_view.load_diff(
            SAMPLE_DIFF,
            existing_threads=[
                ReviewThread(
                    path="auth/jwt.py",
                    line=2,
                    comments=[ThreadComment(author="alice", body="Existing note")],
                )
            ],
        )
        diff_view.add_draft_comment("auth/jwt.py", 2, "my pending note")
        await pilot.pause()

        diff_options = app.query_one("#diff-options", OptionList)
        prompt = str(diff_options.get_option_at_index(2).prompt)
        assert "alice: Existing note" in prompt
        assert "Pending Comment: my pending note" in prompt


@pytest.mark.asyncio
async def test_hide_whitespace_toggle_key():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[_make_mock_scored_pr(101, TriageTier.T0)],
    )
    async with app.run_test() as pilot:
        diff_view = app.query_one("#pr-diff-view", PRDiffView)
        diff_view.load_diff(WS_ONLY_DIFF)
        diff_viewer = app.query_one("#diff-viewer", DiffViewer)
        header = diff_viewer.query_one("#diff-header", Label)
        options = app.query_one("#diff-options", OptionList)

        # Before toggling: the whitespace-only hunk is visible as -/+
        # Before toggling: the whitespace-only hunk is visible as -/+
        assert diff_view.hide_whitespace is False
        assert "whitespace hidden" not in str(header.render())
        assert options.option_count == 4

        await pilot.press("w")
        await pilot.pause()

        assert diff_view.hide_whitespace is True
        assert "whitespace hidden" in str(header.render())
        assert options.option_count == 1  # "no visible changes" note
        assert diff_view.file_diffs[0].hunks == []

        await pilot.press("w")
        await pilot.pause()

        assert diff_view.hide_whitespace is False
        assert "whitespace hidden" not in str(header.render())
        assert options.option_count == 4


@pytest.mark.asyncio
async def test_hide_whitespace_toggle_keeps_real_changes():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[_make_mock_scored_pr(101, TriageTier.T0)],
    )
    async with app.run_test() as pilot:
        diff_view = app.query_one("#pr-diff-view", PRDiffView)
        diff_view.load_diff(WS_INTERLEAVED_DIFF)
        diff_viewer = app.query_one("#diff-viewer", DiffViewer)

        await pilot.press("w")
        await pilot.pause()

        assert diff_view.hide_whitespace is True
        lines = diff_viewer.file_diff.hunks[0].lines
        origins = [line.origin for line in lines]
        assert origins == [" ", " ", "-", "+"]


@pytest.mark.asyncio
async def test_hide_whitespace_noop_without_loaded_diff():
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[_make_mock_scored_pr(101, TriageTier.T0)],
    )
    async with app.run_test() as pilot:
        diff_view = app.query_one("#pr-diff-view", PRDiffView)
        await pilot.press("w")
        await pilot.pause()
        assert diff_view.hide_whitespace is False
        assert "No PR diff loaded" in _status_text(app)


@pytest.mark.asyncio
async def test_thread_fetch_failure_still_displays_diff():
    """A failing review-threads fetch must not prevent the diff from displaying."""

    class FakeClient:
        def __init__(self):
            self.thread_count = 0

        def get_pull_request_diff(self, repo_name_with_owner, pull_number):
            return SAMPLE_DIFF

        def get_pull_request_review_threads(self, repo_name_with_owner, pull_number):
            self.thread_count += 1
            raise RuntimeError("reviews unavailable")

    app = GitkeeperApp(
        config=Config(),
        client=FakeClient(),
        scored_prs=[_make_mock_scored_pr(101, TriageTier.T0)],
    )
    async with app.run_test() as pilot:
        await pilot.pause()
        pr = app.current_scored_pr.pr
        worker = app._fetch_diff_for_pr(pr)
        await worker.wait()
        await pilot.pause()

        diff_viewer = app.query_one("#diff-viewer", DiffViewer)
        assert diff_viewer.file_diff is not None
        assert diff_viewer.file_diff.display_path == "auth/jwt.py"
        options = app.query_one("#diff-options", OptionList)
        assert options.option_count > 0

        pr_key = "acme/backend#101"
        assert app.cached_diffs.get(pr_key) == SAMPLE_DIFF
        assert app.cached_thread.get(pr_key) == []
        assert "Error fetching review threads" in _status_text(app)


def test_rapid_navigation_shutdown_no_lost_exceptions(tmp_path):
    """Rapid queue navigation followed by quit (the real TUI's asyncio.run
    shutdown path) must not leak unhandled asyncio cancellation errors."""
    import subprocess
    import sys
    from pathlib import Path

    repo_root = Path(__file__).parent.parent
    driver = tmp_path / "drive_gitkeeper.py"
    body_lines = []
    for section in range(12):
        body_lines.append(f"### Section {section}")
        for paragraph in range(6):
            body_lines.append(
                f"Paragraph {section}.{paragraph} describing the change "
                "with sufficiently rich detail to slow parsing."
            )
        body_lines.append("- bullet a")
        body_lines.append("- bullet b")
    driver_body = "\\n".join(body_lines)
    driver.write_text(
        f"""\
import asyncio

from textual.await_complete import AwaitComplete
from textual.widgets import Markdown as _Markdown

from gitkeeper.config import Config
from gitkeeper.github.client import PullRequestData
from gitkeeper.scoring.calculator import ScoreBreakdown, TriageTier
from gitkeeper.scoring.pipeline import ScoredPullRequest
from gitkeeper.ui.app import GitkeeperApp

BODY = "{driver_body}"


_orig_update = _Markdown.update


def _slow_update(self, markdown):
    async def slow_update():
        await asyncio.sleep(1.0)
        await _orig_update(self, markdown)
    return AwaitComplete(slow_update())


_Markdown.update = _slow_update


def mock_pr(number, tier):
    pr = PullRequestData(
        id=f"PR_{{number}}", number=number, title=f"PR {{number}}",
        body=BODY, url=f"https://acme/{{number}}",
        repo_name_with_owner="acme/backend", author="alice",
        is_draft=False, state="OPEN",
        created_at="2026-08-14T10:00:00Z", updated_at="2026-08-15T12:00:00Z",
        additions=45, deletions=10, changed_files_count=2, ci_status="SUCCESS",
    )
    score = ScoreBreakdown(tier=tier, affinity_points=50.0, rationale="teammate")
    return ScoredPullRequest(pr=pr, is_actionable=True, score=score)


async def drive(pilot):
    await pilot.press(*(["j"] * 4))
    await pilot.press(*(["k"] * 4))
    await pilot.pause(0.3)
    await pilot.press("q")


scored_prs = [mock_pr(100 + i, TriageTier(i % 4)) for i in range(10)]
app = GitkeeperApp(config=Config(), client=None, scored_prs=scored_prs)
app.run(headless=True, size=(90, 30), auto_pilot=drive)
""",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(driver)],
        capture_output=True,
        text=True,
        cwd=repo_root,
        timeout=180,
    )
    assert result.returncode == 0, result.stderr
    stderr = result.stderr or ""
    assert "never retrieved" not in stderr, stderr
    assert "_GatheringFuture" not in stderr, stderr


@pytest.mark.asyncio
async def test_overview_renders_last_previewed_pr_body():
    def _body(number: int) -> str:
        return f"## PR {number}\n\nDistinct body marker {number} unique content"

    scored_prs = [
        _make_mock_scored_pr_with_body(100 + i, TriageTier(i % 4), _body(100 + i))
        for i in range(6)
    ]
    app = GitkeeperApp(config=Config(), client=None, scored_prs=scored_prs)
    async with app.run_test() as pilot:
        option_list = app.query_one("#pr-option-list", OptionList)
        option_list.focus()
        await pilot.pause()
        for _ in range(len(scored_prs) * 4):
            await pilot.press("j")
            await pilot.pause()
        for _ in range(len(scored_prs) * 4):
            await pilot.press("k")
            await pilot.pause()
        await pilot.pause(0.3)
        markdown = app.query_one("#pr-body-markdown", Markdown)
        last_pr = scored_prs[option_list.highlighted]
        assert f"Distinct body marker {last_pr.pr.number} unique content" in markdown.source


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


def _patch_open_url(monkeypatch):
    opened = []
    monkeypatch.setattr(
        GitkeeperApp,
        "open_url",
        lambda self, url, **kwargs: opened.append(url),
    )
    return opened


def _status_text(app: GitkeeperApp) -> str:
    return app.query_one("#status-bar", Label).content


@pytest.mark.asyncio
async def test_open_browser_key_opens_selected_pr(monkeypatch):
    opened = _patch_open_url(monkeypatch)
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[_make_mock_scored_pr(101, TriageTier.T0)],
    )
    async with app.run_test() as pilot:
        option_list = app.query_one("#pr-option-list", OptionList)
        option_list.focus()
        await pilot.pause()

        await pilot.press("o")
        await pilot.pause()

        assert opened == ["https://github.com/acme/backend/pull/101"]
        assert "Opening https://github.com/acme/backend/pull/101" in _status_text(app)


@pytest.mark.asyncio
async def test_open_browser_no_url_reports(monkeypatch):
    opened = _patch_open_url(monkeypatch)
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[_make_mock_scored_pr(101, TriageTier.T0)],
    )
    async with app.run_test() as pilot:
        await pilot.pause()
        app.current_scored_pr.pr.url = None
        app.action_open_browser()
        await pilot.pause()
        status = _status_text(app)

    assert opened == []
    assert "No URL available" in status


@pytest.mark.asyncio
async def test_open_browser_no_selection_reports(monkeypatch):
    opened = _patch_open_url(monkeypatch)
    app = GitkeeperApp(config=Config(), client=None, scored_prs=[])
    async with app.run_test() as pilot:
        await pilot.pause()
        app.action_open_browser()
        await pilot.pause()
        status = _status_text(app)

    assert opened == []
    assert "No PR selected" in status


@pytest.mark.asyncio
async def test_open_browser_noop_when_modal_open(monkeypatch):
    opened = _patch_open_url(monkeypatch)
    app = GitkeeperApp(
        config=Config(),
        client=None,
        scored_prs=[_make_mock_scored_pr(101, TriageTier.T0)],
    )
    async with app.run_test() as pilot:
        await pilot.pause()
        app.push_screen(InlineCommentModal("auth/jwt.py", 10))
        await pilot.pause()
        app.action_open_browser()
        await pilot.pause()

    assert opened == []
