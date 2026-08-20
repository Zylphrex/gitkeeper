# gitkeeper demo — lightweight GIF for the README (charmbracelet/vhs)
#
# Run from the repo root:
#   vhs demos/readme-demo.tape
#
# Same interaction sequence as demos/gitkeeper-demo.tape (the MP4), shared
# through demos/gitkeeper-steps.tape. Smaller canvas and a faster playback
# speed keep the GIF a reasonable size for the README.

Output demos/gitkeeper-demo.gif

Require ffmpeg
Require ttyd

Set Width 1280
Set Height 720
Set FontSize 16
Set WindowBar Colorful
Set Theme "Dracula"
Set Framerate 20
Set PlaybackSpeed 1.5
Set TypingSpeed 25ms

Source demos/gitkeeper-steps.tape