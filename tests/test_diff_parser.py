from gitkeeper.diff.parser import UnifiedDiffParser
from gitkeeper.diff.whitespace import hide_whitespace

SAMPLE_DIFF = """diff --git a/auth/jwt.py b/auth/jwt.py
index e69de29..d95f3ad 100644
--- a/auth/jwt.py
+++ b/auth/jwt.py
@@ -10,6 +10,7 @@ def verify_token(token: str) -> bool:
     try:
-        payload = jwt.decode(token, SECRET_KEY)
+        jwks = get_jwks()
+        payload = jwt.decode(token, jwks)
         return True
     except Exception:
         return False
diff --git a/README.md b/README.md
new file mode 100644
--- /dev/null
+++ b/README.md
@@ -0,0 +1,3 @@
+# GitKeeper
+
+Terminal PR review tool.
"""


def test_parse_unified_diff():
    file_diffs = UnifiedDiffParser.parse(SAMPLE_DIFF)
    assert len(file_diffs) == 2

    jwt_diff = file_diffs[0]
    assert jwt_diff.old_path == "auth/jwt.py"
    assert jwt_diff.new_path == "auth/jwt.py"
    assert not jwt_diff.is_new
    assert len(jwt_diff.hunks) == 1

    hunk = jwt_diff.hunks[0]
    assert hunk.old_start == 10
    assert hunk.new_start == 10

    lines = hunk.lines
    # Context, deletion, addition, addition, context, context, context
    assert lines[0].origin == " "
    assert lines[0].old_line_no == 10
    assert lines[0].new_line_no == 10

    assert lines[1].origin == "-"
    assert lines[1].old_line_no == 11
    assert lines[1].new_line_no is None

    assert lines[2].origin == "+"
    assert lines[2].old_line_no is None
    assert lines[2].new_line_no == 11
    assert lines[2].content == "        jwks = get_jwks()"

    assert lines[3].origin == "+"
    assert lines[3].new_line_no == 12

    # Second file
    readme_diff = file_diffs[1]
    assert readme_diff.is_new
    assert readme_diff.display_path == "README.md"
    assert len(readme_diff.hunks[0].lines) == 3


WS_TRAILING_DIFF = """diff --git a/auth/jwt.py b/auth/jwt.py
--- a/auth/jwt.py
+++ b/auth/jwt.py
@@ -1,3 +1,3 @@
 import re
-def foo()   
+def foo()
 import sys
"""

WS_REINDENT_DIFF = """\
diff --git a/auth/jwt.py b/auth/jwt.py
--- a/auth/jwt.py
+++ b/auth/jwt.py
@@ -5,2 +5,2 @@
-    old_indent = 1
+  old_indent = 1
-        old_indent2 = 2
+      old_indent2 = 2
"""

WS_INTERLEAVED_DIFF = """\
diff --git a/auth/jwt.py b/auth/jwt.py
--- a/auth/jwt.py
+++ b/auth/jwt.py
@@ -10,5 +10,5 @@
 def verify():
-    return False   
+    return False
-    old_secret = SECRET
+    new_secret = NEW_SECRET
     return True
"""


def test_hide_whitespace_trailing_pair_collapses_to_context():
    file_diffs = UnifiedDiffParser.parse(WS_TRAILING_DIFF)
    hidden = hide_whitespace(file_diffs)

    # The file is kept in the output even though its only hunk fully collapsed.
    assert len(hidden) == 1
    assert len(hidden[0].hunks) == 0


def test_hide_whitespace_whole_file_reindent_collapses():
    file_diffs = UnifiedDiffParser.parse(WS_REINDENT_DIFF)
    hidden = hide_whitespace(file_diffs)
    assert len(hidden) == 1
    assert len(hidden[0].hunks) == 0


def test_hide_whitespace_interleaved_keeps_real_change():
    file_diffs = UnifiedDiffParser.parse(WS_INTERLEAVED_DIFF)
    hidden = hide_whitespace(file_diffs)
    assert len(hidden) == 1
    assert len(hidden[0].hunks) == 1

    lines = hidden[0].hunks[0].lines
    # context, ws-collapsed context, deletion, addition, context
    assert lines[0].origin == " "
    assert lines[0].content == "def verify():"
    assert lines[1].origin == " "
    assert lines[1].content == "    return False"
    assert lines[2].origin == "-"
    assert lines[2].content == "    old_secret = SECRET"
    assert lines[3].origin == "+"
    assert lines[3].content == "    new_secret = NEW_SECRET"
    assert lines[4].origin == " "
    assert lines[4].content == "    return True"


def test_hide_whitespace_preserves_original_line_numbers():
    file_diffs = UnifiedDiffParser.parse(WS_INTERLEAVED_DIFF)
    hidden = hide_whitespace(file_diffs)
    lines = hidden[0].hunks[0].lines

    # The collapsed ws pair takes both sides' original numbers (line 11 → 11).
    assert lines[1].old_line_no == 11
    assert lines[1].new_line_no == 11
    # The real change keeps its numbers too.
    assert lines[2].old_line_no == 12
    assert lines[2].new_line_no is None
    assert lines[3].old_line_no is None
    assert lines[3].new_line_no == 12
    assert lines[4].old_line_no == 13
    assert lines[4].new_line_no == 13


def test_hide_whitespace_leaves_clean_diff_unchanged():
    hidden = hide_whitespace(UnifiedDiffParser.parse(SAMPLE_DIFF))
    assert len(hidden) == 2
    jwt_hunks = hidden[0].hunks[0].lines
    assert [l.origin for l in jwt_hunks] == [" ", "-", "+", "+", " ", " ", " "]
