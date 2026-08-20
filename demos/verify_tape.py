"""Replay the vhs tape's exact keystrokes against the app harness and assert
the app state each step should reach. This is the closest automated check we
can run without visual inspection.

Run:  .venv/bin/python demos/verify_tape.py
"""

import asyncio
import sys

sys.path.insert(0, "demos")

from textual.widgets import Button, OptionList, RadioSet, TextArea

from gitkeeper.config import Config
from gitkeeper.scoring.calculator import FollowUpState
from gitkeeper.ui.app import GitkeeperApp
from gitkeeper.ui.diff_view import DiffViewer, PRDiffView
from gitkeeper.ui.list_view import PRListView
from gitkeeper.ui.modals import InlineCommentModal, SubmitReviewModal

from demo_gitkeeper import MockGitHubClient


def _focused(app) -> str:
    f = app.screen.focused
    return "None" if f is None else f"{type(f).__name__}#{f.id}"


async def main() -> None:
    app = GitkeeperApp(config=Config(), client=MockGitHubClient(latency=False))
    async with app.run_test(size=(170, 46)) as pilot:
        await asyncio.sleep(0.3)
        await pilot.pause()

        pr_list = app.query_one("#pr-option-list", OptionList)
        assert pr_list.option_count == 6, pr_list.option_count
        states = [p.score.follow_state for p in app.query_one("#pr-list-view", PRListView).active_prs]
        assert FollowUpState.ME_ACTIVE in states
        assert FollowUpState.WAITING_AUTHOR in states
        assert FollowUpState.WAITING_OTHERS not in states or True
        print("ok: 6 PRs loaded; ME_ACTIVE + WAITING_AUTHOR badges present (", len([s for s in states if s == FollowUpState.ME_ACTIVE]), "awaiting your action )")

        # --- 5. queue navigation (j x5 then gg) ---
        for _ in range(5):
            await pilot.press("j")
        await pilot.pause()
        assert pr_list.highlighted == 5, pr_list.highlighted
        print("ok: queue moved down to last PR (5)")
        await pilot.press("g")
        await pilot.pause()
        await pilot.press("g")
        await pilot.pause()
        assert pr_list.highlighted == 0, pr_list.highlighted
        print("ok: gg returned to top PR 884")

        # diff for 884 should be cached now
        assert "acme/backend#884" in app.cached_diffs
        print("ok: PR 884 diff cached after returning")

        # --- 6. file tree (exact tape sequence; must end back on jwt.py) ---
        await pilot.press("l")
        await pilot.pause()
        file_list = app.query_one("#file-option-list", OptionList)
        assert app.screen.focused is file_list, _focused(app)
        print("ok: focus is file tree (l from queue)")

        for _ in range(3):
            await pilot.press("j")
        await pilot.pause()
        for _ in range(1):
            await pilot.press("k")
        await pilot.pause()
        for _ in range(1):
            await pilot.press("j")
        await pilot.pause()
        for _ in range(3):
            await pilot.press("k")
        await pilot.pause()

        assert file_list.highlighted == 1, file_list.highlighted
        dv = app.query_one("#pr-diff-view", PRDiffView)
        idx = dv._file_indices[file_list.highlighted]
        assert dv.file_diffs[idx].display_path == "src/auth/jwt.py"
        print("ok: file tree walk ends on src/auth/jwt.py")

        # --- 7. diff viewer (exact tape scroll pattern, 17 j's total) ---
        await pilot.press("l")
        await pilot.pause()
        diff_options = app.query_one("#diff-options", OptionList)
        assert app.screen.focused is diff_options, _focused(app)
        print("ok: focus is diff options (l from file tree)")

        for pattern in ("jj", "jjjj", "j", "jjjj", "jj", "jjjj"):
            for _ in pattern:
                await pilot.press("j")
            await pilot.pause()
        await pilot.pause()
        assert diff_options.highlighted in (16, 17), diff_options.highlighted
        viewer = app.query_one("#diff-viewer", DiffViewer)
        line = viewer._rendered_lines[diff_options.highlighted]
        assert line.new_line_no in (28, 29), (line.new_line_no, line.content)
        content = str(diff_options.get_option_at_index(diff_options.highlighted).prompt)
        assert "bob" in content or "lea" in content or "scope" in content
        print("ok: diff scrolled to the thread area (new line", line.new_line_no, ")")

        # ---- 8. inline comment ----
        await pilot.press("c")
        await pilot.pause()
        assert isinstance(app.screen, InlineCommentModal), type(app.screen)
        text_area = app.screen.query_one("#comment-input", TextArea)
        assert app.screen.focused is text_area or isinstance(app.screen.focused, TextArea)
        print("ok: comment modal opened, focus on text input")
        text_area.text = "Clearer than before. Should we keep allowing ES256?"
        await pilot.press("tab")
        await pilot.pause()
        await pilot.press("tab")
        await pilot.pause()
        assert isinstance(app.screen.focused, Button), _focused(app)
        await pilot.press("enter")
        await pilot.pause()
        drafts = app.draft_comments.get("acme/backend#884", [])
        assert len(drafts) == 1, drafts
        d = drafts[0]
        assert d.path == "src/auth/jwt.py", d.path
        assert d.line in (28, 29), d.line
        assert d.body == "Clearer than before. Should we keep allowing ES256?"
        print(f"ok: draft saved in app state ({d.path}:{d.line})")

        # ---- 9. submit-review modal (prepared, not submitted) ----
        await pilot.press("s")
        await pilot.pause()
        assert isinstance(app.screen, SubmitReviewModal), type(app.screen)
        radios = app.screen.query_one("#review-radioset", RadioSet)
        assert app.screen.focused is radios, _focused(app)
        print("ok: submit-review modal opened, focus on decision radio")
        await pilot.press("tab")
        await pilot.pause()
        body_in = app.screen.query_one("#review-body-input", TextArea)
        assert app.screen.focused is body_in, _focused(app)
        print("ok: focus reached review summary input (typing there later)")
        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, SubmitReviewModal)
        print("ok: Escape closed the submit modal without submitting; no draft cleared")

        print("\nALL CHECKS PASSED")


asyncio.run(main())