# gitkeeper demo — fullscreen MP4 recording (charmbracelet/vhs)
#
# Run from the repo root:
#   vhs demos/gitkeeper-demo.tape
#
# The interaction sequence lives in demos/gitkeeper-steps.tape (shared with
# demos/readme-demo.tape); this tape only adds the MP4 output settings.

Output demos/gitkeeper-demo.mp4

Require ffmpeg
Require ttyd

# --- full screen: a big 1080p terminal so the diff pane has room ---
Set Width 1920
Set Height 1080
Set FontSize 18
Set WindowBar Colorful
Set Theme "Dracula"
Set Framerate 30
Set PlaybackSpeed 1.0
Set TypingSpeed 25ms

Source demos/gitkeeper-steps.tape