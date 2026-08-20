# gitkeeper demo — shared steps, sourced by demos/gitkeeper-demo.tape and
# demos/readme-demo.tape. All paths are relative to this tape file's directory.

# ---------------------------------------------------------------
# 1. call --help straight away
# ---------------------------------------------------------------
Type ".venv/bin/gitkeeper --help"
Enter
Wait+Screen /Usage/
Sleep 3s

# ---------------------------------------------------------------
# 2. full-screen terminal set by the parent; clear the board and start the app
# ---------------------------------------------------------------
Ctrl+L
Sleep 400ms

Type ".venv/bin/python demos/demo_gitkeeper.py"
Enter

# ---------------------------------------------------------------
# 3-4. gitkeeper boots. The mock GitHub client answers after a few
#      seconds, so the loading state stays in the recording.
# ---------------------------------------------------------------
Wait+Screen@30s /#101/
Sleep 1.5s

# ---------------------------------------------------------------
# 5. walk the PR queue — every row badge is a different follow-up state
# ---------------------------------------------------------------
Type "j"
Sleep 2.5s
Type "j"
Sleep 2.5s
Type "j"
Sleep 2.5s
Type "j"
Sleep 2.5s
Type "j"
Sleep 2.5s

# back to the top PR (diffs are cached now, so this snaps back)
Type "gg"
Sleep 1.2s

# ---------------------------------------------------------------
# 6. focus the file tree and hop between the changed files, then
#    land back on src/auth/jwt.py
# ---------------------------------------------------------------
Type "l"
Sleep 700ms
Type "j"
Sleep 1.2s
Type "j"
Sleep 1.2s
Type "j"
Sleep 1.2s
Type "k"
Sleep 600ms
Type "j"
Sleep 600ms
Type "k"
Sleep 600ms
Type "k"
Sleep 600ms
Type "k"
Sleep 600ms

# ---------------------------------------------------------------
# 7. focus the diff and scroll the file itself down to line 29,
#    where an existing review thread already sits
# ---------------------------------------------------------------
Type "l"
Sleep 600ms
Type "jj"
Sleep 350ms
Type "jjjj"
Sleep 350ms
Type "j"
Sleep 350ms
Type "jjjj"
Sleep 350ms
Type "jj"
Sleep 350ms
Type "jjjj"
Sleep 800ms

# ---------------------------------------------------------------
# 8. leave an inline comment on that line
# ---------------------------------------------------------------
Type "c"
Sleep 600ms
Type "Clearer than before. Should we keep allowing ES256?"
Sleep 250ms
Tab
Tab
Enter
Sleep 1.2s

# ---------------------------------------------------------------
# 9. prepare to submit a review… but stop short of submitting
# ---------------------------------------------------------------
Type "s"
Sleep 900ms
Tab
Type@50ms "Nice work — approving once the scope check is covered by a test."
Sleep 900ms
Escape
Sleep 1.5s

# ---------------------------------------------------------------
# done
# ---------------------------------------------------------------
Type "q"
Sleep 1.2s