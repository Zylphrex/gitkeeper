from gitkeeper.diff.parser import UnifiedDiffParser

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
