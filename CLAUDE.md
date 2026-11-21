# CLAUDE.md

This repo is a Claude skill (`SKILL.md` is the entry point) that computes Jewel Gate probability heatmaps from screenshots. Read `SKILL.md`, then `references/lessons.md`, before changing anything.

## Commands

- `python3 scripts/selftest.py` : regression test. Run after ANY change to `screen.py`, `read_board.py`, `analyze.py`, `widget.py` or `solve.py`. It must print `ALL PASSED`.
- `python3 scripts/analyze.py IMG.png --outdir out` : the one-command pipeline (read, solve, widget, reply text).
- `python3 scripts/level.py N --widget out.html` : blank-board map for a level.
- Dependencies: Python 3, numpy, pillow, scipy. List file names explicitly when calling scripts (no brace expansion in `/bin/sh`).

## Standing rules (user requirements, do not regress)

1. Every board reply: ONE inline widget with the crop from that screenshot beside the gem list, the **found count** ("k of N found") and **each gem's size (rows x cols)**, then the **heatmap**. The heatmap is always generated, even when every square is tied.
2. The crop's colours must match the screenshot (hidden = magenta (214,0,255); found gems keep their own colour). Never reduce the palette.
3. The crop data must not be garbled: keep the run-length canvas format, decode-check it before writing the widget, and paste `widget.html` verbatim from `cat` output (never retype or reuse an older string).
4. No standard gem sizes: take sizes from `levels/levels.json` or the user, never from sprites or another level.
5. User corrections beat the reader ("mark r3c5 as blank" = `--add-dug r3c5`). Cells never un-dig; use `--prev`.
6. Do not lengthen replies: tables, one question ("Does this match your screen?").

## When you change something

- Keep `SKILL.md`, `README.md`, `CLAUDE.md`, `references/lessons.md` and `references/screenshot-reading.md` in sync with the code. A new behaviour, flag, level or colour belongs in the docs in the same commit.
- A new failure or user correction goes into `references/lessons.md` (cause, fix) and, if it is a standing rule, into the list above and `SKILL.md`.
- Add a fixture to `tests/fixtures` and an entry to `tests/expected.json` for every new reader case; add example specs with an `expect` block to `examples/`.
- Levels 4-5 now have real fixtures (IMG_2775/2781/2820 = level 4, IMG_2821/2822 = level 5). Add a fixture for every new case: a hit (partly revealed gem), a new found colour, a new level layout.
- Geometry (`screen.GEOM`), check-mark positions and the artwork box are for the iPhone portrait screenshot (1125x2436).

## Delivering

- Before editing, `git clone https://github.com/nadavcoh/jewel-gate-heatmap.git` (public; `jewl-gate-heatmap` is the old name and redirects) and work from that clone, not from a stale copy of the skill. Read-only tools of the connector are not needed for that.
- If `gh-push-mcp` answers "Not Found" for the repo or for `main`, the session is usually stale or flaky: retry (a cheap `create_branch main` returning "Reference already exists" proves it can see the repo) or reconnect the connector; do not conclude the repo is missing.
- Push to `nadavcoh/jewel-gate-heatmap`, branch `main`, with real git and the `gh-push-mcp` `git_credentials` tool (write mode): short-lived token passed through `http.extraheader`, never printed or stored, no force-push, no branch deletion.
- Deliver code as a **zip**, never tar.gz (saved user preference).
- Commit messages: one line saying what changed and why.
