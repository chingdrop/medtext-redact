# Terminal recording for the README. Render from the repo root:
#
#   vhs docs/demo.tape
#
# Needs vhs (https://github.com/charmbracelet/vhs) plus its ttyd and ffmpeg
# dependencies, and `uv sync` already run. The output is the real CLI's real
# output on a synthetic note from tools/gen_fixtures.py; nothing here is
# scripted text. PAGER=cat keeps --verbose from opening a pager mid-recording.
#
# vhs 0.12 with ffmpeg 9 exits 0 but silently writes no GIF (its own ffmpeg
# call fails). Workaround: point Output at a directory ("Output frames/") to
# get PNG frames, then assemble them yourself:
#
#   ffmpeg -framerate 50 -i frames/frame-text-%05d.png \
#     -framerate 50 -i frames/frame-cursor-%05d.png \
#     -filter_complex "[0][1]overlay,crop=iw:620:0:0,scale=iw/2:-2:flags=lanczos,pad=iw+48:ih+48:24:24:color=0x171717,tpad=stop_mode=clone:stop_duration=6,fps=12,split[a][b];[a]palettegen[p];[b][p]paletteuse" \
#     docs/demo.gif
#
# On a Retina display the frames come out at 2x; the filter crops the empty
# rows below the output, scales back to 1x, adds padding, and holds the final
# frame for 6 seconds so the result can be read.

Output docs/demo.gif

Set Shell "bash"
Set FontSize 16
Set Width 1400
Set Height 440
Set Padding 24
Set TypingSpeed 45ms

# Start from a clean state (not recorded): a short prompt on its own line (the
# generated notes have no trailing newline), no continuation prompt, an
# up-to-date environment so uv prints nothing, and a config file.
Hide
Type `export PS1=$'\n$ ' PS2='' PAGER=cat && cd $(git rev-parse --show-toplevel) && uv sync -q && rm -rf /tmp/demo && mkdir -p /tmp/demo && echo '{"Masking": {}}' > /tmp/demo/config.json && clear`
Enter
Show

Type "uv run python tools/gen_fixtures.py --seed 7 --count 4 --out-dir /tmp/demo"
Sleep 400ms
Enter
Sleep 2s

Type "cat /tmp/demo/notes/note_0003.txt"
Sleep 400ms
Enter
Sleep 3s

Type "uv run medtext-redact parse-report -c /tmp/demo/config.json single -v \"
Enter
Type `  -t "$(cat /tmp/demo/notes/note_0003.txt)" \`
Enter
Type `  -k amoxicillin -k "chronic kidney disease"`
Sleep 600ms
Enter

# Loading spaCy's model takes a few seconds; then hold on the result.
Sleep 8s
Sleep 4s
